from django import forms

class UploadForm(forms.Form):
    
    url = forms.URLField(label='', required=False,widget=forms.URLInput(attrs={'placeholder': 'URL de l\'image', 'class': 'form-control col ms-3 mb-3'}))
    file = forms.FileField(label='u', required=False, widget=forms.ClearableFileInput(attrs={'accept': 'image/*','id': 'file','type':'file', 'class': 'btn col_blue ms-3 mb-3'}))
    password = forms.CharField(label='', required=False, widget=forms.TextInput(attrs={'placeholder': 'Mot de passe (optionnel)', 'class': 'form-control mb-3'}))
    file_wordlist = forms.FileField(label='', required=False, widget=forms.ClearableFileInput(attrs={'accept': '.txt','id':'wordlist', 'class': 'btn col_blue mb-3'}))

    exif= forms.BooleanField(label='Exiftool', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    steghide= forms.BooleanField(label='Steghide', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    zsteg= forms.BooleanField(label='Zsteg', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    strings= forms.BooleanField(label='Strings', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    stegsolve= forms.BooleanField(label='Stegsolve', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    binwalk= forms.BooleanField(label='Binwalk', required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    foremost= forms.BooleanField(label='Foremost', required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    File= forms.BooleanField(label='File', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))
    metadata= forms.BooleanField(label='Metadata', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}))

    def clean_valid(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        file = cleaned_data.get('file')
        
        if not url and not file:
            raise forms.ValidationError("Veuillez fournir une image via l'URL ou le fichier.")
        return cleaned_data