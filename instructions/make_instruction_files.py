import os

os.chdir('templates/instructions')
os.system("rm InstructionPage*")
for i in range(13):
    os.system(f"cp template.html InstructionPage_{i+1:02d}.html")