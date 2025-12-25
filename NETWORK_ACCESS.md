# Guide d'accès réseau - OACA

Ce guide explique comment accéder à l'application OACA depuis plusieurs ordinateurs sur le même réseau.

## Configuration actuelle

Le serveur Flask est configuré pour écouter sur **toutes les interfaces réseau** (`0.0.0.0`), ce qui permet l'accès depuis d'autres machines.

## Démarrage du serveur

### Option 1: Utiliser le script de démarrage (Recommandé)

**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Python (tous systèmes):**
```bash
python start_server.py
```

Le script affichera automatiquement les adresses IP disponibles.

### Option 2: Démarrer manuellement

```bash
python app.py
```

## Trouver votre adresse IP

### Windows:
```bash
ipconfig
```
Cherchez "Adresse IPv4" dans la sortie.

### Linux/Mac:
```bash
ifconfig
# ou
ip addr show
```

## Accès depuis d'autres ordinateurs

1. **Assurez-vous que tous les ordinateurs sont sur le même réseau** (même Wi-Fi ou réseau local)

2. **Trouvez l'adresse IP du serveur** (voir ci-dessus)

3. **Depuis un autre ordinateur**, ouvrez un navigateur et accédez à:
   ```
   http://[ADRESSE_IP]:8000
   ```
   Par exemple: `http://192.168.1.100:8000`

## Configuration du pare-feu

### Windows:
1. Ouvrez "Pare-feu Windows Defender"
2. Cliquez sur "Paramètres avancés"
3. Créez une nouvelle règle entrante pour le port 8000 (TCP)

### Linux (ufw):
```bash
sudo ufw allow 8000/tcp
```

### Linux (firewalld):
```bash
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

## Exemple d'utilisation

- **PC Admin** (192.168.1.100): Lance le serveur
- **PC Candidat 1** (192.168.1.101): Accède via `http://192.168.1.100:8000`
- **PC Candidat 2** (192.168.1.102): Accède via `http://192.168.1.100:8000`

## Dépannage

### Le serveur ne répond pas depuis d'autres machines:

1. Vérifiez que le serveur écoute sur `0.0.0.0` (déjà configuré)
2. Vérifiez que le pare-feu autorise le port 8000
3. Vérifiez que les machines sont sur le même réseau
4. Essayez de ping l'adresse IP du serveur depuis l'autre machine

### Changer le port:

Si le port 8000 est déjà utilisé, vous pouvez changer le port:

**Windows:**
```bash
set PORT=8080
python app.py
```

**Linux/Mac:**
```bash
export PORT=8080
python app.py
```

## Sécurité

⚠️ **Important**: En production, n'utilisez pas `debug=True` et configurez un serveur WSGI approprié (comme Gunicorn ou uWSGI) avec HTTPS.

