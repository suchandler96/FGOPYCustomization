import os, shutil, re

PATCH_VER = "v20.2.1"

assert os.path.exists("fgoImage"), f"Please run this script ({os.path.abspath(__file__)}) under {os.path.join('FGO-py', 'FGO-py')} directory."
if not os.path.exists(os.path.join("fgoImage", "slash.png")):
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slash.png"), os.path.join("fgoImage", "slash.png"))

os.system("cd " + os.path.dirname(os.path.abspath(__file__)) + " && git pull")
os.system("git reset --hard origin/master")
os.system("git apply " + os.path.join(os.path.dirname(os.path.abspath(__file__)), f"diff_{PATCH_VER}.patch"))
if os.path.exists("customizedTurn.py"):
    with open("customizedTurn.py") as f:
        cus_lines = f.readlines()
    class_name = None
    for line in cus_lines:
        if class_name_match := re.search("^class\s+(\w+)\(.+\):", line):
            class_name = class_name_match.group(1)
            break
    assert class_name != "Turn", "Your customized turn class should not be named 'Turn'."
    if class_name is not None:
        print(f"Customized Turn class found: {class_name}, adding it to fgoKernel.py...")
        with open("fgoKernel.py", "r+") as f:
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
