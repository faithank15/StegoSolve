import os
import re
import logging
from io import BytesIO
import requests
from django.shortcuts import render
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from PIL import Image, UnidentifiedImageError
import exifread
import struct
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from .forms import UploadForm
import subprocess

# ---------------- Helper Functions ----------------

def save_image_to_media(filename, content):
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{get_random_string(8)}{ext}"
    path = os.path.join('uploads', filename)
    return default_storage.save(path, ContentFile(content))

# ---------- EXIF & Metadata Extraction -----------

def get_exif(image_path):
    try:
        out = subprocess.run(["/usr/bin/exiftool", image_path], capture_output=True, text=True, check=True)
        output = out.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [f"Error running exiftool: {e}"]
    return output


def get_metadata(image_path):
    try:
        out = subprocess.run(["/usr/bin/mediainfo", image_path], capture_output=True, text=True, check=True)
        output = out.stdout.strip().splitlines()
        return output
    except subprocess.CalledProcessError as e:
        return [f"Error running mediainfo: {e}"]

# -------------- Strings Extraction ---------------

def extract_strings_from_bytes(bytes_data, min_length=4):
    pattern = b"[ -~]{%d,}" % min_length
    found = re.findall(pattern, bytes_data)
    return [s.decode('utf-8', errors='ignore') for s in found]

# --------------- Python StegSolve ----------------
"""L'effet de stegsolve a été reproduit à partir de l'emploi de pillow jumellé à numpy pour extraire les différentes couches de l'image."""
def get_color_channels(img: Image.Image):
    r, g, b = img.split()
    return {'Red': r, 'Green': g, 'Blue': b}

def extract_bit_plane(channel: Image.Image, bit: int) -> Image.Image:
    return channel.point(lambda p: ((p >> bit) & 1) * 255)

def get_all_bit_planes(img: Image.Image):
    planes = {}
    for name, ch in get_color_channels(img).items():
        for bit in range(8):
            planes[(name, bit)] = extract_bit_plane(ch, bit)
    return planes

def invert_image(img: Image.Image) -> Image.Image:
    return img.point(lambda p: 255 - p)

def to_grayscale(img: Image.Image) -> Image.Image:
    return img.convert('L')


def steg_layers(img_path: str):
    img = Image.open(img_path).convert('RGB')

    layers = {}

    layers.update(get_color_channels(img))
    
    layers.update({f'{c}_bit{b}': p for (c,b), p in get_all_bit_planes(img).items()})
    
    layers['invert'] = invert_image(img)
    
    layers['grayscale'] = to_grayscale(img)
    
    return layers
# ---------------- Zsteg ----------------
def zsteg_extract(image_path: str):
    try:
        out = subprocess.run(["zsteg", image_path, "-E", "all"], capture_output=True, text=True)
        output = out.stdout.strip()
        return output.splitlines()
    except subprocess.CalledProcessError as e:
        return [f"Error running zsteg: {e}"]
# ---------------- Steghide ----------------

def key_from_passphrase(passphrase: str) -> bytes:
    return sha256(passphrase.encode('utf-8')).digest()

def decrypt_message(blob: bytes, key: bytes) -> bytes:
    (length,) = struct.unpack(">I", blob[:4])
    iv = blob[4:20]
    ct = blob[20:20+length]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

def extract_lsb(stego_path, num_bytes: int) -> bytes:
    img = Image.open(stego_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    pixels = img.load()
    bits = []
    total_bits = num_bytes * 8

    for y in range(h):
        for x in range(w):
            if len(bits) >= total_bits:
                break
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
        if len(bits) >= total_bits:
            break

    data = bytearray()
    for i in range(0, total_bits, 8):
        byte = bits[i:i+8]
        data.append(int(''.join(byte), 2))
    return bytes(data)

def reveal_with_passphrase(stego_img, passphrase: str) -> str:
    key = key_from_passphrase(passphrase)
    try:
        header = extract_lsb(stego_img, 4 + 16)
        (ct_len,) = struct.unpack(">I", header[:4])
        total = 4 + 16 + ct_len
        blob = extract_lsb(stego_img, total)
        pt = decrypt_message(blob, key)
        return pt.decode('utf-8')
    except (ValueError, struct.error) as e:
        raise ValueError("Mauvaise passphrase ou pas de message caché.") from e


def run_steghide(stego_img, passphrase=None, wordlist=None) -> str:
    try:
        if passphrase:
            out=subprocess.run(["steghide", "extract", "-sf", stego_img, "-p", passphrase], capture_output=True, text=True)
            output=out.stdout.strip().splitlines()
            return '\n'.join(output) if output else "Aucun message caché trouvé avec cette passphrase."
        if wordlist:
            out=subprocess.run(['stegseek', '-f', wordlist, stego_img], capture_output=True, text=True)
            output=out.stdout.strip().splitlines()
            return '\n'.join(output) if output else "Aucun message caché trouvé avec cette wordlist."
        out=subprocess.run(["steghide", "extract", "-sf", stego_img, "-p", ''], capture_output=True, text=True)
        output=out.stdout.strip().splitlines()
        return '\n'.join(output) if output else "Aucun message caché trouvé sans passphrase."
    except Exception as e:
        return f"Erreur lors de l'exécution de steghide: {e}"
# def run_steghide(stego_img, passphrase=None,wordlist=None) -> str:
#     print("Info contextuel ::::::::::",passphrase,wordlist)
#     if passphrase:
#         print(":::::::pass:::::")
#         try:
#             print("step 1")
#             return reveal_with_passphrase(stego_img,passphrase)
#         except ValueError as e :
#             print("::::::::::step 2")
#             print(e)
#             return f'{e}'
#     if wordlist:
#         print(":::::::::::step 3")
#         with open(wordlist, "rb") as f:
#             list = f.readlines()
#         try:
#             for c in list:
#                 secret = reveal_with_passphrase(stego_img,c)
#                 if secret :
#                     return f'La passphrase {c} est valide pour ce message caché : \n {secret}'
#         except :
#             return 'Aucun passphrase correspondant'
#     return False
            

# ---------------- binwalk via API ----------------

def run_binwalk(image_path):
    try:
        out = subprocess.run(["binwalk", image_path],capture_output=True, text=True)
        return out.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [f"Error running binwalk: {e}"]

def pngcheck(image_path):
    try:
        out = subprocess.run(["pngcheck", image_path], capture_output=True, text=True, check=True)
        output = out.stdout.strip().splitlines()
        return output
    except subprocess.CalledProcessError as e:
        return [f"Error running pngcheck: {e}"]

def jpeginfo(image_path):
    try:
        out = subprocess.run(["jpeginfo", "-c", image_path], capture_output=True, text=True, check=True)
        output = out.stdout.strip().splitlines()
        return output
    except subprocess.CalledProcessError as e:
        return [f"Error running jpeginfo: {e}"]

def run_file(path):
    image_path = os.path.join(settings.MEDIA_ROOT, path)
    try:
        out = subprocess.run(["file", image_path], capture_output=True, text=True, check=True)
        output = out.stdout.strip().split(':')
        return output[1].strip() if len(output) > 1 else "Unknown file type"
    except subprocess.CalledProcessError as e:
        return f"Error running file: {e}"

# --------------- Foremost Alternative ----------------


# --------------- HTMX's GET Views ----------------

@require_GET
def analyse_exif(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    exif = get_exif(full)
    return render(request, 'steg_app/partials/exif.html', {'exif': exif})

@require_GET
def analyse_zsteg(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    zsteg = zsteg_extract(full)
    return render(request, 'steg_app/partials/zsteg.html', {'zsteg' : zsteg})

@require_GET
def analyse_metadata(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    metadata = get_metadata(full)
    return render(request, 'steg_app/partials/meta.html', {'metadata': metadata})

@require_GET
def analyse_strings(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    with open(full, 'rb') as f:
        data = f.read()
    strings = extract_strings_from_bytes(data)
    return render(request, 'steg_app/partials/strings.html', {'strings': strings})

@require_GET
def analyse_stegsolve(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    
    layers = steg_layers(full)
    return render(request, 'steg_app/partials/stegsolve.html', {'layers': layers})

@require_GET
def analyse_steghide(request):
    rel = request.GET.get('path')
    pasw = request.GET.get('password')
    wd = request.GET.get('wordlist')
    wd_l = ''
    if wd :
        wd_l = os.path.join(settings.MEDIA_ROOT, wd)
    full = os.path.join(settings.MEDIA_ROOT, rel)
    output = []
    output.append(run_steghide(full,pasw,wd_l))
   
    return render(request, 'steg_app/partials/steghide.html', {'steghide': output})

@require_GET
def analyse_binwalk(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    output = run_binwalk(full)
    return render(request, 'steg_app/partials/binwalk.html', {'binwalk': output})

@require_GET
def analyse_foremost(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    out_path = os.path.join(settings.MEDIA_ROOT, 'foremost_output')
    try:
        out = subprocess.run(["foremost", "-i", full, "-o", out_path], capture_output=True, text=True, check=True)
        audit_file = os.path.join(out_path, "audit.txt")
        with open(audit_file, "r", encoding="utf-8", errors="ignore") as f:
            report = f.read()
        return render(request, 'steg_app/partials/foremost.html', {'foremost': report.splitlines()})
    except subprocess.CalledProcessError as e:
        return render(request, 'steg_app/partials/foremost.html', {'foremost': [f"Error running foremost: {e}"]})

@require_GET
def analyse_file(request):
    output = run_file(request.GET.get('path'))
    return render(request, 'steg_app/partials/file.html', {'File': output})    
    
@require_GET
def analyse_pngcheck(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    output = pngcheck(full)
    return render(request, 'steg_app/partials/pngcheck.html', {'pngcheck': output})

@require_GET
def analyse_jpeginfo(request):
    rel = request.GET.get('path')
    full = os.path.join(settings.MEDIA_ROOT, rel)
    output = jpeginfo(full)
    return render(request, 'steg_app/partials/jpeginfo.html', {'jpeginfo': output})

# ------------------ Main Upload View ----------------

def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            
            if not form.cleaned_data.get('url') and not form.cleaned_data.get('file'):
                form.add_error(None, "Veuillez fournir une image via l'URL ou le fichier.")
                return render(request, 'steg_app/upload.html', {'form': form})
            
            
            url_field = form.cleaned_data.get('url')
            file_field = form.cleaned_data.get('file')
            password = form.cleaned_data.get('password')
            wordlist = form.cleaned_data.get('file_wordlist')
            exif= form.cleaned_data.get('exif')
            steghide= form.cleaned_data.get('steghide')
            zsteg= form.cleaned_data.get('zsteg')
            strings= form.cleaned_data.get('strings')
            stegsolve= form.cleaned_data.get('stegsolve')
            binwalk= form.cleaned_data.get('binwalk')
            foremost= form.cleaned_data.get('foremost')
            File= form.cleaned_data.get('File')
            metadata= form.cleaned_data.get('metadata')
            
            # Récupère et sauvegarde l'image
            if url_field:
                resp = requests.get(url_field, timeout=5)
                resp.raise_for_status()
                image_content = resp.content
                fname = url_field.split('/')[-1]
            else:
                image_content = file_field.read()
                fname = file_field.name

            relpath = save_image_to_media(fname, image_content)
            image_url = settings.MEDIA_URL + relpath

            # Sauvegarde la wordlist si présente
            wl_rel = ''
            if wordlist:
                wl_bytes = wordlist.read()
                wl_rel = save_image_to_media(wordlist.name, wl_bytes)

            # Récupère le type de fichier
            img = Image.open(os.path.join(settings.MEDIA_ROOT, relpath))
            file_type = img.format

            if file_type == "PNG":
                pngcheck=True
            
            if file_type == "JPEG":
                jpeginfo=True
            
            if not any([exif, steghide, zsteg, strings, stegsolve, binwalk, foremost, File]):
                form.add_error(None, "Veuillez sélectionner au moins une méthode d'analyse.")
                return render(request, 'steg_app/upload.html', {'form': form})

            context = {
                'saved_path': relpath,
                'image_url': image_url,
                'password': password or '',
                'wordlist': wl_rel or '',
                'exif': exif,
                'steghide': steghide,
                'zsteg': zsteg,
                'strings': strings,
                'stegsolve': stegsolve,
                'binwalk': binwalk,
                'foremost': foremost,
                'File': File,
                'form': form,
                'pngcheck': pngcheck if 'pngcheck' in locals() else False,
                'jpeginfo': jpeginfo if 'jpeginfo' in locals() else False,
                'metadata': metadata,
            }
            return render(request, 'steg_app/results.html', context)
    else:
        form = UploadForm()
    return render(request, 'steg_app/upload.html', {'form': form})
