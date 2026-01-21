import os, shutil, re
import argparse
from tokenizer import generateCustomizedTurn

PATCH_VER = "v20.2.1"
FGOPY_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../FGO-py/"))

def parse_args():
    parser = argparse.ArgumentParser(description="Install script for FGO-py customization")
    parser.add_argument("--install-file", "-f", type=str, default="", help="File used to generate or get already-written customized turn class")
    parser.add_argument("--fgo-py-root-dir", required=False, default=FGOPY_ROOT_DIR, type=str, help="Path to FGO-py directory")
    return parser.parse_args()

args = parse_args()
fgo_py_dir = os.path.join(args.fgo_py_root_dir, "FGO-py")
slash_png_path = os.path.join(fgo_py_dir, "fgoImage", "slash.png")

if not os.path.exists(slash_png_path):
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slash.png"), slash_png_path)

if args.install_file == "":
    custom_py_file = ""
elif not args.install_file.endswith(".py"):
    custom_py_file = "generatedCustomTurn.py"
    with open(custom_py_file, "w", encoding="utf-8") as f:
        f.write(generateCustomizedTurn(args.install_file))
    print("Customized turn class generated to generatedCustomTurn.py")
else:
    custom_py_file = args.install_file

os.system("cd " + os.path.dirname(os.path.abspath(__file__)) + " && git pull")
os.system("cd " + fgo_py_dir + " && git reset --hard origin/master")
os.system("cd " + fgo_py_dir + " && git apply " + os.path.join(os.path.dirname(os.path.abspath(__file__)), f"diff_{PATCH_VER}.patch"))
if custom_py_file == "":
    pass
elif os.path.exists(custom_py_file):
    with open(custom_py_file, encoding="utf-8") as f:
        cus_lines = f.readlines()
    class_name = None
    for line in cus_lines:
        if class_name_match := re.search("^class\s+(\w+)\(.+\):", line):
            class_name = class_name_match.group(1)
            break
    assert class_name != "Turn", "Your customized turn class should not be named 'Turn'."
    if class_name is not None:
        print(f"Customized Turn class found: {class_name}, adding it to fgoKernel.py...")
        with open(os.path.join(fgo_py_dir, "fgoKernel.py"), "r+", encoding="utf-8") as f:
            battle_class_line = 0
            lines = f.readlines()
            for i, line in enumerate(lines):
                if battle_class_match := re.search(r"class\s+Battle\s*:", line):
                    battle_class_line = i
                if "def __init__(self,turnClass=Turn):" in line:
                    lines[i] = f"    def __init__(self,turnClass={class_name}):\n"
                    break
            f.seek(0)
            f.truncate()
            f.writelines(lines[:battle_class_line])
            f.write("\n# Customized Turn\n")
            for cl in cus_lines:
                if len(cl) > 0 and re.search(r"^import", cl) is None and re.search(r"^from.+import.+", cl) is None:
                    f.write(cl)
            f.write("\n")
            f.writelines(lines[battle_class_line:])
else:
    print(f"Customized turn file {custom_py_file} not found! Skipping customized turn installation.")
