import ast, os, shutil, re, platform
import argparse
from tokenizer import generateCustomizedTurn

PATCH_VER = "v21.1.1"
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

def parse_custom_file(path):
    """Return (names of all top-level classes in the file, the file's lines without its import statements)."""
    with open(path, encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"In {path}: syntax error ({e}).")
        return [], []
    class_names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    # drop top-level (possibly multi-line) import statements, the names they bring in already exist in fgoKernel.py
    import_lines = {n for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
                    for n in range(node.lineno, node.end_lineno + 1)}
    code_lines = [line for n, line in enumerate(source.splitlines(keepends=True), 1) if n not in import_lines]
    if code_lines and not code_lines[-1].endswith("\n"):
        code_lines[-1] += "\n"
    return class_names, code_lines

def main():
    args = parse_args()
    fgo_py_dir = os.path.join(args.fgo_py_root_dir, "FGO-py")
    slash_png_path = os.path.join(fgo_py_dir, "fgoImage", "slash.png")

    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slash.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendrightbar.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendclassscoreslashplusfat.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendclassscoreslashplusthin.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendclassscorenormalplus.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunareisousymbol.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunareisoutonp.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizuna10.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizuna15.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunaclothes.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunaorderedfemale.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunaorderedkind.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunarider.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kizunastarorevil.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendclassscorerecttop.png"), os.path.join(fgo_py_dir, "fgoImage"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "findfriendhougulevelkeywordcn.png"), os.path.join(fgo_py_dir, "fgoImage", "cn"))
    shutil.move(os.path.join(fgo_py_dir, "fgoImage", "cn", "findfriendhougulevelkeywordcn.png"), os.path.join(fgo_py_dir, "fgoImage", "cn", "findfriendhougulevelkeyword.png"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "99.png"), os.path.join(fgo_py_dir, "fgoImage", "map", "entrance"))
    shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "login"), os.path.join(fgo_py_dir, "fgoImage", "login"), dirs_exist_ok=True)   # auto login images, incl. login/flag
    shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "grandBattle"), os.path.join(fgo_py_dir, "fgoImage", "map", "grandBattle"), dirs_exist_ok=True)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_99.png"), os.path.join(fgo_py_dir, "fgoImage", "map"))
    shutil.move(os.path.join(fgo_py_dir, "fgoImage", "map", "map_99.png"), os.path.join(fgo_py_dir, "fgoImage", "map", "99.png"))   # rename

    os.system("cd " + os.path.dirname(os.path.abspath(__file__)) + " && git pull")
    os.system("cd " + fgo_py_dir + (" && git reset --hard origin/master" if platform.system() != "Windows" else "") + " && git apply " +
              os.path.join(os.path.dirname(os.path.abspath(__file__)), f"diff_{PATCH_VER}.patch"))

    valid_files = translate_and_get_valid_files(args.install_files) if args.install_files else []

    to_add_lines = []
    to_install_turns = set()
    for custom_py_file in valid_files:
        class_names, code_lines = parse_custom_file(custom_py_file)
        if not class_names:
            print(f"In {custom_py_file}: No valid customized Turn class found. Skipping...")
            continue
        if "Turn" in class_names:
            print(f"In {custom_py_file}: Your customized turn class should not be named 'Turn'. Skipping this file...")
            continue
        duplicates = [name for name in class_names if name in to_install_turns]
        assert not duplicates, f"Duplicate customized Turn class name: {duplicates} (found again in {custom_py_file})"
        print(f"Customized Turn class(es) found in {custom_py_file}: {', '.join(class_names)}, adding to fgoKernel.py...")
        to_install_turns.update(class_names)
        to_add_lines.extend(code_lines)
        to_add_lines.append("\n")

    # The default Turn class of Battle is left untouched, customized turns are selected through the quest config (turnClass)
    with open(os.path.join(fgo_py_dir, "fgoKernel.py"), "r+", encoding="utf-8") as f:
        battle_class_line = 0
        lines = f.readlines()
        for i, line in enumerate(lines):
            if re.search(r"class\s+Battle\s*:", line):
                battle_class_line = i
                break
        f.seek(0)
        f.truncate()
        f.writelines(lines[:battle_class_line])
        f.write("\n# Customized Turns\n")
        f.writelines(to_add_lines)
        f.writelines(lines[battle_class_line:])

if __name__ == "__main__":
    main()
