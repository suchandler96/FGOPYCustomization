import os, shutil, re
import argparse
from tokenizer import generateCustomizedTurn

PATCH_VER = "v21.0.2"
FGOPY_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../FGO-py/"))

def parse_args():
    parser = argparse.ArgumentParser(description="Install script for FGO-py customization")
    parser.add_argument("--install-files", "-f", nargs='*', help="Files used to generate or get already-written customized turn class")
    parser.add_argument("--fgo-py-root-dir", required=False, default=FGOPY_ROOT_DIR, type=str, help="Path to FGO-py directory")
    return parser.parse_args()

def translate_and_get_valid_files(input_files):
    valid_files = []
    for file in input_files:
        if os.path.exists(file):
            if file.endswith(".py"):
                valid_files.append(os.path.abspath(file))
            else:
                generated_file = file[:file.rfind('.')] + ".py"
                with open(generated_file, "w", encoding="utf-8") as f:
                    f.write(generateCustomizedTurn(file))
                print(f"Custom Turn class generated: {file} -> {generated_file}")
                valid_files.append(generated_file)
        else:
            print(f"Customized turn file {file} not found! Skipping...")
    return valid_files

def main():
    args = parse_args()
    fgo_py_dir = os.path.join(args.fgo_py_root_dir, "FGO-py")
    slash_png_path = os.path.join(fgo_py_dir, "fgoImage", "slash.png")

    if not os.path.exists(slash_png_path):
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slash.png"), os.path.join(fgo_py_dir, "fgoImage"))

    os.system("cd " + os.path.dirname(os.path.abspath(__file__)) + " && git pull")
    os.system("cd " + fgo_py_dir + " && git reset --hard origin/master && git apply " +
              os.path.join(os.path.dirname(os.path.abspath(__file__)), f"diff_{PATCH_VER}.patch"))

    valid_files = translate_and_get_valid_files(args.install_files) if args.install_files else []

    to_add_lines = []
    default_turn_class = "Turn"
    to_install_turns = set()
    for custom_py_file in reversed(valid_files):
        with open(custom_py_file, encoding="utf-8") as f:
            cus_lines = f.readlines()
        class_name = None
        for line in cus_lines:
            if class_name_match := re.search("^class\s+(\w+)\(.+\):", line):
                class_name = class_name_match.group(1)
                break
        if class_name == "Turn":
            print(f"In {custom_py_file}: Your customized turn class should not be named 'Turn'.")
            continue
        elif class_name is not None:
            print(f"Customized Turn class found: {class_name}, adding it to fgoKernel.py...")
            default_turn_class = class_name
            assert class_name not in to_install_turns, f"Duplicate customized Turn class name: {class_name}"
            to_install_turns.add(class_name)
            for cl in cus_lines:
                if len(cl) > 0 and re.search(r"^import", cl) is None and re.search(r"^from.+import.+", cl) is None:
                    to_add_lines.append(cl)
            to_add_lines.append("\n")
        else:
            print(f"In {custom_py_file}: No valid customized Turn class found. Skipping...")

    with open(os.path.join(fgo_py_dir, "fgoKernel.py"), "r+", encoding="utf-8") as f:
        battle_class_line = 0
        lines = f.readlines()
        for i, line in enumerate(lines):
            if battle_class_match := re.search(r"class\s+Battle\s*:", line):
                battle_class_line = i
            if "def __init__(self,turnClass=Turn):" in line:
                lines[i] = f"    def __init__(self,turnClass={default_turn_class}):\n"
                break
        f.seek(0)
        f.truncate()
        f.writelines(lines[:battle_class_line])
        f.write("\n# Customized Turns\n")
        f.writelines(to_add_lines)
        f.writelines(lines[battle_class_line:])
    print(f"Setting {default_turn_class} as the default Turn class of --turnClass command in fgoCli.py...")
    with open(os.path.join(fgo_py_dir, "fgoCli.py"), "r+", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "--turnClass" in line:
                lines[i] = re.sub(r"default=.*\)", f"default='{default_turn_class}')", line)
        f.seek(0)
        f.truncate()
        f.writelines(lines)

if __name__ == "__main__":
    main()
