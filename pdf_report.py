import json, os

from pypdf import PdfWriter

from reportlab.pdfgen import canvas 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.pdfbase import pdfmetrics

config = json.load(open("config.json"))

start_y = 770
mass_error_thresh = config["qc_thresholds"]["mass_error_thresh"]
rt_error_thresh = config["qc_thresholds"]["rt_error_thresh"]
med_cv_thresh = config["qc_thresholds"]["med_cv_thresh"]
mean_corr_thresh = config["qc_thresholds"]["mean_corr_thresh"]

def place_measure(pdf, label, value, x, y, bold=False, red=False):
    if bold:
        pdf.setFont('ArialBd', 11)
        pdf.drawString(x, y, label)
        pdf.setFont('Arial', 11)
    else:
        pdf.drawString(x, y, label)
    if red:
        pdf.setFillColorRGB(140,0,0)
        pdf.drawRightString(x + 230, y, str(value))
        pdf.setFillColorRGB(0,0,0)
    else:
        pdf.drawRightString(x + 230, y, str(value))

def write_column(pdf, pairs, x, start_y):
    y_pos = start_y
    for pair in pairs:
        if len(pair) == 3:
            args = pair.pop(2)
            place_measure(pdf, pair[0], pair[1], x, y_pos, bold=args["bold"], red=args["red"])
        else:
            place_measure(pdf, pair[0], pair[1], x, y_pos)
        y_pos -= 20

def set_args(measure = None, threshold = None, bar = False, bold = False, red = False):
    args = {"bold": bold, "red": red}
    if measure and threshold:
        if (bar and measure < threshold) or (not bar and measure > threshold):
            args["red"] = True
    return args

def get_target_img_pairs(qc):
    files = os.listdir(qc.mzxml_dir)
    images = []
    for file in files:
        if file[-4:] == ".jpg":
            images += [file]
    img_pairs = []
    for i in range(0, int(len(images)/2)):
        img_pairs += [[images[i*2], images[i*2+1]]]
    return img_pairs

def make_target_page(pdf, qc, img_pair):
    pdf.setFont('ArialBd', 14)
    num, name, filetype = img_pair[0].split("_")
    pdf.drawCentredString(300, 760, f"Target #{num}: {name}")
    pdf.drawInlineImage(qc.mzxml_dir + "/" + img_pair[0], 150, 450, width=300,height=300) 
    pdf.drawInlineImage(qc.mzxml_dir + "/" + img_pair[1], 150, 100, width=300,height=300)
    pdf.showPage()

def none_round(num, decimals=0):
    if num == None:
        return num
    elif decimals == 0:
        return round(num)
    else:
        return round(num, decimals)

def write_report(qc):
    title = f"{qc.study_dir} {qc.method}"
    pdf = canvas.Canvas(qc.mzxml_dir + "/qc_report.pdf")
    pdf.setTitle(title)
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    pdfmetrics.registerFont(TTFont('ArialBd', 'ArialBd.ttf'))
    pdf.setFont('ArialBd', 14)
    pdf.drawCentredString(300, 810, "QC Short Report")
    pdf.setFont('Arial', 14)
    pdf.drawCentredString(300, 795, title)
    pdf.setFont('Arial', 11)
    y_pos = start_y
    col1 = [
        ["Number of samples:", qc.num_samples],
        ["Start:", qc.runtimes["start_time"]],
        ["End:", qc.runtimes["end_time"]],
        ["", ""],
        ["Mass Spec:", qc.machine_info["msModel"]],
        ["Minimum scans:", qc.scan_stats["min"]],
        ["Mean scans:", none_round(qc.scan_stats["mean"])],
        ["Maximum scans:", qc.scan_stats["max"]],
        ["Number of peaks:", qc.peaks["num"]],
        ["Number nonzero peaks:", qc.peaks["nonzero"]],
        ["Number peaks in 90% samples:", qc.peaks["present90per"]],
        ["Number peaks in 50% samples:", qc.peaks["present50per"]],
        ["Mean median intensity:", none_round(qc.mean_median_intensity)],
        ["",""],
        ["Sample Replicability","", set_args(bold=True)],
        [
            "Minimum mean pairwise Pearson R:",
            none_round(qc.replicability["sample-wise"]["min_mean_correlation"], 3),
            set_args(measure=qc.replicability["sample-wise"]["min_mean_correlation"], threshold=mean_corr_thresh, bar=True)
        ],
        [
            "Median mean pairwise Pearson R:",
            none_round(qc.replicability["sample-wise"]["median_mean_correlation"], 3),
            set_args(measure=qc.replicability["sample-wise"]["median_mean_correlation"], threshold=mean_corr_thresh, bar=True)
        ],
        [
            "Maximum mean pairwise Pearson R:",
            none_round(qc.replicability["sample-wise"]["max_mean_correlation"], 3),    
            set_args(measure=qc.replicability["sample-wise"]["max_mean_correlation"], threshold=mean_corr_thresh, bar=True),
        ]
    ]
    col2 = [
        ["Target Matching","", set_args(bold=True)],
        ["Targets matched:", qc.target_stats["targets_matched"]],
        ["Number of matches:", qc.target_stats["num_matches"]],
        ["Duplicated matches:", qc.target_stats["duplicate_matches"]],
        [
            "Median mass error (ppm):",
            none_round(qc.target_stats["median_mass_error"], 2),
            set_args(measure=qc.target_stats["median_mass_error"], threshold=mass_error_thresh)
        ],
        [
            "Maximum mass error (ppm):",
            none_round(qc.target_stats["max_mass_error"], 2),
            set_args(measure=qc.target_stats["max_mass_error"], threshold=mass_error_thresh)
        ],
        [
            "Median RT error (s):",
            none_round(qc.target_stats["median_rt_error"]),
            set_args(measure=qc.target_stats["median_rt_error"], threshold=rt_error_thresh)
        ],
        [
            "Maximum RT error (s):",
            none_round(qc.target_stats["max_rt_error"]),
            set_args(measure=qc.target_stats["max_rt_error"], threshold=rt_error_thresh)
        ],
        ["",""],
        ["Feature Replicability","", set_args(bold=True)],
        [
            "Minimum median CV:",
            none_round(qc.replicability["feature-wise"]["min_median_cv"], 2),
            set_args(measure=qc.replicability["feature-wise"]["min_median_cv"], threshold=med_cv_thresh)
        ],
        [
            "Median median CV:",
            none_round(qc.replicability["feature-wise"]["median_median_cv"], 2),
            set_args(measure=qc.replicability["feature-wise"]["median_median_cv"], threshold=med_cv_thresh)
        ],
        [
            "Maximum median CV:",
            none_round(qc.replicability["feature-wise"]["max_median_cv"], 2),
            set_args(measure=qc.replicability["feature-wise"]["max_median_cv"], threshold=med_cv_thresh)
        ],
        ["Minimum median QRscore:", none_round(qc.replicability["feature-wise"]["min_median_qrscore"], 2)],
        ["Median median QRscore:", none_round(qc.replicability["feature-wise"]["median_median_qrscore"], 2)],
        ["Maximum median QRscore:", none_round(qc.replicability["feature-wise"]["max_median_qrscore"], 2)]
    ]
    write_column(pdf, col1, 50, start_y)
    write_column(pdf, col2, 320, start_y)
    pdf.showPage()
    img_pairs = get_target_img_pairs(qc)
    for pair in img_pairs:
        make_target_page(pdf, qc, pair)
    pdf.save()

def merge_reports(qc):
    merger = PdfWriter()
    merger.append(qc.mzxml_dir + "/qc_report.pdf")
    merger.append(qc.mzxml_dir + "/Rplots.pdf")
    merger.write(qc.mzxml_dir + "/qc_report.pdf")
    merger.close()