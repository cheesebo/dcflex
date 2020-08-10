import re
from datetime import datetime, date, timedelta

from azure.cosmosdb.table.models import Entity
from azure.cosmosdb.table.tableservice import TableService
from flask import Flask, render_template, request
app = Flask(__name__)
#Using Azure table called flexitime in Storge account dcflexitime
table_service = TableService(account_name='dcflexitime', account_key='/p3DS6YsABpZP9ll9xgPo8H2vuH4Jd7Q8q2wZDOnC10kDaSsEdYm2U1DTIACzscyyj12gmxQ+qX458CG+P/2tw==')

#Global variables:
date_today = ''
current_start_date = ''
current_hours = 0
reg_run_hours = 0
diff_hours = 0

def getflexidata():
    "Returns all flexitime data"
    global date_today, current_start_date,  current_hours,  reg_run_hours,  diff_hours
    #Get todays date:
    now = datetime.now() # current date and time
    date_today = now.strftime("%d/%m/%Y")
    #Read start date and hours
    flexidata = table_service.get_entity('flexitime', 'flexitime', '001')
    current_start_date=flexidata.startdate
    current_hours=flexidata.hours
    if current_hours == '':
        current_hours = 0
    current_hours = float(current_hours)
    #Number of days into FlexRun (don't count weekends)
    start_date_obj = datetime.strptime(current_start_date , '%d/%m/%Y')
    #delta = datetime.now() - start_date_obj
    daygenerator = (start_date_obj + timedelta(x + 1) for x in range((datetime.now() - start_date_obj).days))
    delta = sum(day.weekday() < 5 for day in daygenerator)
    #Add 1 for today!
    run_days = delta + 1
    reg_run_hours = run_days * 7.5
    diff_hours = current_hours - reg_run_hours
    return

@app.route("/")
def home():
    global date_today, current_start_date,  current_hours,  reg_run_hours,  diff_hours
    getflexidata()
    return render_template(
        "home.html",
        date_today=date_today,
        current_start_date=current_start_date,
        current_hours=current_hours,
        reg_run_hours=reg_run_hours,
        diff_hours=diff_hours,
    )

@app.route("/start_reset", methods=['GET','POST'])
def start_reset():
    global date_today, current_start_date,  current_hours,  reg_run_hours,  diff_hours
    #Get todays date:
    #now = datetime.now() # current date and time
    #date_today = now.strftime("%d/%m/%Y")
    #Read start date and hours
    #flexidata = table_service.get_entity('flexitime', 'flexitime', '001')
    #current_start_date=flexidata.startdate
    #current_hours=flexidata.hours
    getflexidata()
    if request.method == 'POST':
        new_date = request.form['set_date']
        current_hours = 0
        if not new_date:
            current_start_date=(date_today)
        else:
            #Validate the string
            try:
                date_obj = datetime.strptime(new_date , '%d/%m/%Y')
            except ValueError:
                return render_template(
                    "start_reset.html",
                    current_start_date=current_start_date,
                    date_today=date_today,
                    current_hours=current_hours,
                    oops="Date format should be dd/mm/YYYY" 
                )
            current_start_date=(new_date)
        #Update start date and current hours
        flexidata={'PartitionKey': 'flexitime', 'RowKey': '001', 'startdate': current_start_date, 'hours': current_hours}
        table_service.insert_or_replace_entity('flexitime', flexidata)
    return render_template(
        "start_reset.html",
        current_start_date=current_start_date,
        date_today=date_today,
        current_hours=current_hours,
        oops=""
    )

@app.route("/enter_hours/", methods=['GET', 'POST'])
def enter_hours():
    global date_today, current_start_date,  current_hours,  reg_run_hours,  diff_hours
    oops=""
    getflexidata()
    if request.method == 'POST':
        add_hours=request.form['add_hours']        
        #Validate the string
        try:
            current_hours = current_hours + float(add_hours)
            diff_hours = current_hours - float(reg_run_hours)
            current_hours_str = "{:.2f}".format(current_hours)
            #Update current hours
            flexidata={'PartitionKey': 'flexitime', 'RowKey': '001', 'startdate': current_start_date, 'hours': current_hours_str}
            table_service.insert_or_replace_entity('flexitime', flexidata)
        except ValueError:
            oops="Please only enter a number" 
    return render_template(
        "enter_hours.html",
        date_today=date_today,
        current_start_date=current_start_date,
        current_hours=current_hours,
        reg_run_hours=reg_run_hours,
        diff_hours=diff_hours,
        oops=oops
    )
