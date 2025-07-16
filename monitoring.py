import smtplib, json, sqlite3, time
from email.mime.text import MIMEText
import pandas as pd

from utilities import check_file_sequence

# https://mailtrap.io/blog/python-send-email-gmail/#Send-email-in-Python-using-Gmail-SMTP
# must turn on 2-step verification for sending Gmail and then get an application password
# save this password in config["password"]

con = sqlite3.connect("./db/qc_results.db", check_same_thread=False)
cur = con.cursor()

config = json.load(open("monitoring_config.json"))

def send_email(subject, body, sender = config["sender"], recipients = config["recipients"], password = config["password"]):
    msg = MIMEText(body, _charset="UTF-8")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

def should_check_qc():
    last_entry = cur.execute("SELECT id FROM sampleQC ORDER BY id DESC LIMIT 1").fetchall()[0][0]
    last_file = cur.execute(f"SELECT file_name FROM sampleQC WHERE id == '{last_entry}'").fetchall()[0][0]
    if last_entry == config["last_sample"] or 'blank' in last_file:
        return False, last_entry, last_file
    else:
        return True, last_entry, last_file

def check_qc(last_entry, mode):
    tic = cur.execute(f"SELECT tic FROM sampleQC WHERE id == '{last_entry}'").fetchall()[0][0]
    tic_flag = tic > config[mode]["tic_thresh"]
    intStd_matches = pd.read_sql_query(f"SELECT * FROM intStdMatches WHERE sampleID == '{last_entry}'", con)
    num_targets = len(intStd_matches)
    intStd_matches = intStd_matches[intStd_matches["intensity"] > config[mode]["intensity_thresh"]][intStd_matches["apex_intensity"] > config[mode]["apex_thresh"]]
    is_flag = len(intStd_matches) / num_targets >= config[mode]["min_percent_targets"]
    return tic_flag, is_flag

def compose_message(mode):
    table = "TIC\t\tIS\t\t\tFile Name"
    tics = ["Pass" if x == True else "Fail" for x in config[mode]['tic_strikes']]
    intstds = ["Pass" if x == True else "Fail" for x in config[mode]['is_strikes']]
    for i in range(0, 5):
        table += f"\n{tics[i]}\t\t{intstds[i]}\t\t" + config[mode]["last_samples"][i]
    message = f"QC of {mode} has failed. \n\n" + table
    return message

def reset_config():
    modes = ["hilicpos", "c18neg"]
    for mode in modes:
        if config[mode]["emails_sent"] > 0:
            config[mode]["tic_strikes"] = [True, True, True, True, True]
            config[mode]["is_strikes"] = [True, True, True, True, True]
            config[mode]["emails_sent"] = 0
    json.dump(config, open("monitoring_config.json", "w"), indent=4)



#resetting monitor config on restart
reset_config()

while True:
    try:
        time.sleep(300)
        should_check, last_entry, last_file = should_check_qc()
        mode = check_file_sequence(last_file)
        if should_check:
            tic_flag, is_flag = check_qc(last_entry, mode)
            _old = config[mode]["tic_strikes"].pop(0)
            _old = config[mode]["is_strikes"].pop(0)
            _old = config[mode]["last_samples"].pop(0)
            config[mode]["tic_strikes"] += [tic_flag]
            config[mode]["is_strikes"] += [is_flag]
            file_dir = cur.execute(f"SELECT path FROM sampleQC JOIN experiment ON experimentID = experiment.id WHERE sampleQC.id == '{last_entry}'").fetchall()[0][0]
            config[mode]["last_samples"] += [file_dir + "\\" + last_file]
            print(f"Checked file: {config[mode]['last_samples'][4]}")
            if sum(config[mode]["tic_strikes"]) < 4 or sum(config[mode]["is_strikes"]) < 4:
                if config[mode]["emails_sent"] < 3:
                    send_email(config["subject_line"], compose_message(mode))
                    config[mode]["emails_sent"] += 1
            config["last_sample"] = last_entry
            json.dump(config, open("monitoring_config.json", "w"), indent=4)
    except KeyboardInterrupt:
        print("Monitor loop ended.")
        break
