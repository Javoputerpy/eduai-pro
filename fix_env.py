import os

env_path = '.env'
token = '8759146939:AAEonBdrCFxH9R9yiwcx0kEVUcAEKJpmUv4'

# Read current content safely if possible
content = ""
if os.path.exists(env_path):
    with open(env_path, 'rb') as f:
        raw_data = f.read()
        # Remove null characters and try to decode
        clean_data = raw_data.replace(b'\x00', b'')
        try:
            content = clean_data.decode('utf-8')
        except:
            content = clean_data.decode('latin-1')

# Add or update token
lines = content.splitlines()
new_lines = []
found = False
for line in lines:
    if line.startswith('TELEGRAM_BOT_TOKEN='):
        new_lines.append(f'TELEGRAM_BOT_TOKEN={token}')
        found = True
    elif line.strip():
        new_lines.append(line)

if not found:
    new_lines.append(f'TELEGRAM_BOT_TOKEN={token}')

with open(env_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines) + '\n')

print("Fixed .env with proper encoding.")
