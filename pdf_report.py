from reportlab.pdfgen import canvas 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.pdfbase import pdfmetrics 
from reportlab.lib import colors 

qc = "foo"

def place_measure(pdf, label, value, x, y):
    pdf.drawString(x, y, label)
    pdf.drawRightString(x + 200, y, str(value))

title = f"QC Short Report: {qc.study_dir} {qc.method}"
pdf = canvas.Canvas(qc.mzxml_dir + "/qc_report.pdf")
pdf.setTitle(title)
pdfmetrics.registerFont(
    TTFont('arial', 'Arial.ttf')
)
pdf.setFont('arial', 14)
pdf.drawCentredString(300, 800, title)
pdf.setFont('arial', 11)
start_y = 780
pairs = [
    ["Number of samples:", qc.num_samples],
    ["Start:", qc.runtimes["start_time"]],
    ["End:", qc.runtimes["end_time"]],
    ["", ""],
    ["Mass Spec:", qc.machine_info["msModel"]],
    ["Minimum scans:", qc.scan_stats["min"]],
    ["Mean scans:", round(qc.scan_stats["mean"])],
    ["Maximum scans:", qc.scan_stats["max"]],
    ["Number of peaks:", qc.peaks["num"]],
    ["Number nonzero peaks::", qc.peaks["nonzero"]],
    ["Number peaks in 90% samples:", qc.peaks["present90per"]],
    ["Number peaks in 50% samples:", qc.peaks["present50per"]],
    ["",""],
    ["Targets matched:", qc.target_stats["targets_matched"]],
    ["Number of matches:", qc.target_stats["num_matches"]],
    ["Duplicated matches:", qc.target_stats["duplicate_matches"]],
    ["Mean mass error (ppm):", round(qc.target_stats["mean_mass_error"], 3)],
    ["Maximum mass error (ppm):", round(qc.target_stats["max_mass_error"], 3)],
    ["Mean RT error (s):", round(qc.target_stats["mean_rt_error"])],
    ["Maximum RT error (s):", round(qc.target_stats["max_rt_error"])],
    ["",""],
    ["Mean median intensity:", round(qc.mean_median_intensity)],
    ["Feature Replicability",""],
    ["Minimum median CV:", qc.replicability["feature-wise"]["min_median_cv"]]
]
for pair in pairs:
    place_measure(pdf, pair[0], pair[1], 50, start_y)
    start_y -= 20
pdf.save()

