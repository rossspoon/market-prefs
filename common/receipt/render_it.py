import pdflatex
from jinja2 import Template
from datetime import datetime

KEEP = True

base_data = [
    ['34T', 10, 2],
    ['09B', 10, 23],
    ['66H', 10, 15],
    ['29N', 10, 8],
    ['32Q', 10, 0],
]


def full_data(d):
    show = f"\\${d[1]:.2f}"
    bonus = f"\\${d[2]:.2f}"
    total = f"\\${d[1] + d[2]:.2f}"

    return dict(label=d[0], show_up=show, bonus=bonus, total=total)


data = [full_data(d) for d in base_data]

now = datetime.now()
date_str = now.strftime('%A  %m/%d/%Y')
with open('receipt_temp.tex', 'r') as f:
    template_str = f.read()

t = Template(template_str)
tex = t.render(data=data, date=date_str)

pdfl = pdflatex.PDFLaTeX.from_binarystring(tex.encode(), 'boogy')
pdf, log, cp = pdfl.create_pdf(keep_pdf_file=KEEP, keep_log_file=False)
