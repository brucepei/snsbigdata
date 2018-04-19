from django.core.management.base import BaseCommand, CommandError
from tbd.models import Build,TestResult,Project,TestAction,Host
import xlwt,ConfigParser,datetime,os

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.db.models import Sum

class Command(BaseCommand):
    help="this is command help"
    def add_arguments(self, parser):
        #parser.add_argument('sp_name', nargs='+', type=str, help="pass sp name")
        parser.add_argument('--sp_name',default=None,help='Please input SP name')
        parser.add_argument('--owner',default='QCA9886',help='Please input test owner')
    def handle(self, *args, **options):
        all_sp_build=[]
        send_users=[]
        if options.get('owner',None):
            send_users=options['owner'].replace("\'",'').split(';')
        if options.get('sp_name',None):
            cbd_project=Project.objects.get(name=options['sp_name'])
            running_build=cbd_project._attr.split(';')
            for pj_attr in running_build:
                if pj_attr.startswith('running_build'):
                    bld_id=int(pj_attr.split('=')[1])
                    cbd_build=Build.objects.get(id=bld_id)
                    test_result=cbd_build.testresult_set.all()
                    all_sp_build.append(test_result)
        else:
            dir_path=os.getcwd()
            config_file_path='tbd\management\commands\check_action_result.ini'
            config_file_path=os.path.join(dir_path,config_file_path)
            order_project_sp=get_config(config_file_path)
            for bld in order_project_sp:
                send_users.extend(bld[2])
                send_users=list(set(send_users))
                try:
                    cbd_build=Build.objects.get(version=bld[1])
                    test_result=cbd_build.testresult_set.all()
                    all_sp_build.append(test_result)
                except:
                    print 'build is invalid'
        result_file=write_xlsfile(all_sp_build)
        send_mail(os.path.join(os.getcwd(),result_file),send_users)#['c_lishuj@qti.qualcomm.com'])
        print send_users
        

def get_config(config_file):
    cf = ConfigParser.ConfigParser()
    cf.read(config_file)
    projects=cf.sections()
    print '>>>>>>>>>>>>>>',projects
    collect_arr=[]
    for project in projects:
        owner = cf.get(project, "owner")
        owner = owner.split(';')
        for i in xrange(len(owner)):
            owner[i]=owner[i] + '@qti.qualcomm.com'
        sp = cf.get(project, "sp")
        collect_arr.append((project,sp,owner))
    print collect_arr
    return collect_arr
        
def write_xlsfile(all_build_result=None):
    if all_build_result:
        wb=xlwt.Workbook()
        for mode_obj in all_build_result:
            if not mode_obj:
                continue
            wb_sheet=wb.add_sheet(mode_obj[0].build.project.name.replace('.','_'))
            wb_sheet.write(0,0,'build')
            wb_sheet.write(0,1,'test_action')
            wb_sheet.write(0,2,'pass_count')
            wb_sheet.write(0,3,'fail_count')
            check_act_result={}
            for i in range(1,len(mode_obj)+1):
                if mode_obj[i-1].testaction.name not in check_act_result:
                    check_act_result[mode_obj[i-1].testaction.name]=[mode_obj[i-1].pass_count,mode_obj[i-1].fail_count]
                else:
                    check_act_result[mode_obj[i-1].testaction.name][0]+=mode_obj[i-1].pass_count
                    check_act_result[mode_obj[i-1].testaction.name][1]+=mode_obj[i-1].fail_count
            testaction_count=len(check_act_result.keys())
            wb_sheet.write_merge(1,testaction_count,0,0,mode_obj[0].build.version) #merge from 1,0 to 4,0
            i=1
            for dic_result in check_act_result:
                wb_sheet.write(i,1,dic_result)
                wb_sheet.write(i,2,check_act_result[dic_result][0])
                wb_sheet.write(i,3,check_act_result[dic_result][1])
                i+=1
        get_time=str(datetime.datetime.now()).replace(' ','_').replace(':','_')[:19]
        wb.save('{}_test_act_result.xls'.format(get_time))
        
        wb2=xlwt.Workbook()
        for mode_obj in all_build_result:
            if not mode_obj:
                continue
            wb_sheet2=wb2.add_sheet(mode_obj[0].build.project.name.replace('.','_'))
            wb_sheet2.write(0,0,'build')
            wb_sheet2.write(0,1,'host')
            wb_sheet2.write(0,2,'test_action')
            wb_sheet2.write(0,3,'pass_count')
            wb_sheet2.write(0,4,'fail_count')
            check_act_result={}
            action_pass = mode_obj.values_list("host_id","testaction").annotate(Sum("pass_count"))
            action_fail = mode_obj.values_list("host_id","testaction").annotate(Sum("fail_count"))
            host_ac_pass_keys = {}
            host_ac_faill_keys = {}
            host_id_c=[]
            ac_id_c=[]
            for i in action_pass:
                h_id, ac_id, p_acc = i
                host_id_c.append(h_id)
                ac_id_c.append(ac_id)
                if (h_id, ac_id) not in host_ac_pass_keys.keys():
                    host_ac_pass_keys.update({(h_id, ac_id):p_acc})
            
            for i in action_fail:
                h_id, ac_id, p_acc = i
                host_id_c.append(h_id)
                ac_id_c.append(ac_id)
                if (h_id, ac_id) not in host_ac_faill_keys.keys():
                    host_ac_faill_keys.update({(h_id, ac_id):p_acc})
            
            ac_id_c=list(set(ac_id_c))
            host_id_c=list(set(host_id_c))
            ac_id_name={}
            host_id_name={}
            for i in ac_id_c:
                ac_id_name[i]=TestAction.objects.get(id=i).name
            
            for i in host_id_c:
                host_id_name[i]=Host.objects.get(id=i).name
            
            end_result={}
            p_ks = host_ac_pass_keys.keys()
            f_ks = host_ac_faill_keys.keys()
            p_ks.extend(f_ks)
            p_ks=list(set(p_ks))
            for i in p_ks:
                if i[0] not in end_result:
                    end_result[i[0]]=[]
                end_result[i[0]].append((i[1],host_ac_pass_keys.get(i,0),host_ac_faill_keys.get(i,0)))
                
            print end_result
            #{host_id:[(1,2,3)]}
            

            build_len = len(p_ks)
            wb_sheet2.write_merge(1,build_len,0,0,mode_obj[0].build.version)
            
            clum_=1
            start_clu=1
            i=1
            for dic_result in end_result:
                ac_len=len(end_result[dic_result])
                print host_id_name[dic_result]
                wb_sheet2.write_merge(start_clu,ac_len+start_clu-1,1,1,str(host_id_name[dic_result]))
                start_clu+=ac_len
                print '+++++++++++++++'
                print dic_result
                print end_result[dic_result]
                print '============'
                for j in end_result[dic_result]:
                    wb_sheet2.write(i,2,ac_id_name[j[0]])
                    wb_sheet2.write(i,3,j[1])
                    wb_sheet2.write(i,4,j[2])
                    i+=1
            
        get_time2=str(datetime.datetime.now()).replace(' ','_').replace(':','_')[:19]
        wb2.save('{}_test_act_result_2.xls'.format(get_time2))
        
        return '{}_test_act_result.xls'.format(get_time)
        
def send_mail(file_path,receiveduser):
    smtpserver = 'sdc-cnss-ds1'
    username='admin'
    password='t-span'
    senduser='admin@sdc-cnss-ds1.qca.qualcomm.com'
    receiveduser=','.join(receiveduser)

    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'CBD test status'
    msgRoot['From']=senduser
    msgRoot['To']=receiveduser

    xlsxpart = MIMEApplication(open(file_path, 'rb').read())
    xlsxpart.add_header('Content-Disposition', 'attachment', filename='test_result.xls')
    msgRoot.attach(xlsxpart)

    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username,password)
    smtp.sendmail(senduser,receiveduser,msgRoot.as_string())
    smtp.quit()
