import os
import shutil

src_root = "/home/debanshhota/SuRaksha-Setu"
dest_root = os.path.join(src_root, "deploy-online")

print(f"Creating deploy-online root at: {dest_root}")
os.makedirs(dest_root, exist_ok=True)
os.makedirs(os.path.join(dest_root, "backend"), exist_ok=True)
os.makedirs(os.path.join(dest_root, "ml-service"), exist_ok=True)

# 1. Copy backend files
print("Copying backend files...")
shutil.copytree(os.path.join(src_root, "src"), os.path.join(dest_root, "backend", "src"), dirs_exist_ok=True)
shutil.copy(os.path.join(src_root, "pom.xml"), os.path.join(dest_root, "backend", "pom.xml"))
shutil.copy(os.path.join(src_root, "Dockerfile"), os.path.join(dest_root, "backend", "Dockerfile"))

# 2. Copy ml-service files
print("Copying ml-service files...")
shutil.copy(os.path.join(src_root, "forensic_engine.py"), os.path.join(dest_root, "ml-service", "forensic_engine.py"))
shutil.copy(os.path.join(src_root, "behavioral_analytics_engine.py"), os.path.join(dest_root, "ml-service", "behavioral_analytics_engine.py"))
shutil.copy(os.path.join(src_root, "utils.py"), os.path.join(dest_root, "ml-service", "utils.py"))
shutil.copy(os.path.join(src_root, "ml-service", "requirements.txt"), os.path.join(dest_root, "ml-service", "requirements.txt"))
shutil.copy(os.path.join(src_root, "ml-service", "Dockerfile.forensic"), os.path.join(dest_root, "ml-service", "Dockerfile.forensic"))
shutil.copy(os.path.join(src_root, "ml-service", "Dockerfile.behavioral"), os.path.join(dest_root, "ml-service", "Dockerfile.behavioral"))

# 3. Copy admin-dashboard files (excluding node_modules and build artifacts)
print("Copying admin-dashboard files...")
dashboard_src = os.path.join(src_root, "admin-dashboard")
dashboard_dest = os.path.join(dest_root, "admin-dashboard")

def ignore_patterns(path, names):
    ignored = []
    for name in names:
        if name in ['node_modules', '.next', 'out', 'build', '.git']:
            ignored.append(name)
    return ignored

shutil.copytree(dashboard_src, dashboard_dest, ignore=ignore_patterns, dirs_exist_ok=True)

# 4. Copy .env.example
shutil.copy(os.path.join(src_root, "infra", ".env.example"), os.path.join(dest_root, ".env.example"))

print("✅ File structure copied successfully!")
