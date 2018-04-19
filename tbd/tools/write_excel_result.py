import xlwt,datetime
from django.db.models import Sum
from tbd.models import Build,TestResult,Project,TestAction,Host

def write_excel(all_build_result):
    print "111111111111111111"
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
        wb_sheet2.write(0,5,'rate_pass')
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
                wb_sheet2.write(i,5,str(round(float(j[1])/float(j[1]+j[2])*100,2)) + '%')
                i+=1
        
    get_time2=str(datetime.datetime.now()).replace(' ','_').replace(':','_')[:19]
    #wb2.save('{}_test_act_result_2.xls'.format(get_time2))
    return wb2