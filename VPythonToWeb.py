file = open("finalProject.py").read()
file = file.replace("import vpython", "")
file = file.replace("vpython.", "")
web = open("web.txt", 'w')
web.write('Web VPython 3.2' + file)