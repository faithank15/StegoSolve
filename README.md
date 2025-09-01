# 🕵️‍♂️ StegApp – Plateforme d’analyse stéganographique

StegApp est une application web Django permettant d’analyser des images à la recherche de données cachées.  
Elle intègre plusieurs outils de stéganalyse connus et s’exécute entièrement via **Docker**, pour garantir une installation simple et sécurisée.

---

## 🚀 Fonctionnalités principales

- **Envoi d’image**
  - Upload depuis l’ordinateur
  - Saisie d’une URL

- **Outils disponibles**
  - `exiftool` → extraction des métadonnées classiques (date, GPS, appareil photo, etc.)
  - `steghide` → recherche de données cachées avec mot de passe ou wordlist
  - `zsteg` → analyse bitplanes pour PNG
  - `strings` → recherche de chaînes de texte lisibles dans le fichier
  - `stegsolve` → inspection visuelle des plans de couleur
  - `binwalk` → recherche de fichiers ou signatures intégrés
  - `foremost` → extraction automatique de fichiers cachés ou supprimés
  - `file` → identification précise du type de fichier
  - `metadata` → inspection avancée des métadonnées

- **Interface web (Django + Bootstrap)**
  - Formulaire simple et intuitif
  - Résultats affichés directement dans la page
  - Navigation claire avec section “Comment ça marche ?”

---

## 📦 Installation

### 1. Installer Docker

Si vous n’avez pas Docker, suivez ces instructions :

- **Windows / Mac / Linux**  
  Téléchargez [Docker Desktop](https://docs.docker.com/get-started/get-docker) et installez-le selon votre OS.

  Vérifiez l’installation :

  `docker --version`
  `docker-compose --version`

---

### 2. Cloner le projet

`git clone https://github.com/faithank15/StegoSolve.git`
`cd StegoSolve/stegoSolve`

---

### 3. Construire l’image Docker

`docker build -t dockerfile .`

---

### 4. Lancer le conteneur

`docker run -it --rm -p 8080:8000 dockerfile:latest`

---

### 5. Accéder à l’application

Ouvrez votre navigateur sur : http://127.0.0.1:8080/
