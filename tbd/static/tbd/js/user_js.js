(function($) {
    $.fn.getDataAttrs = function() {
        var attributes = {}; 
        if( this.length ) {
            $.each( this[0].attributes, function( index, attr ) {
                if (attr.name.indexOf("data-") == 0 && attr.name.length > 5) {
                    attributes[ attr.name.substr(5) ] = attr.value;
                }
            } ); 
        }
        return attributes;
    };
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                //alert($("#csrfmiddlewaretoken").val());
                xhr.setRequestHeader("X-CSRFToken", $("#csrfmiddlewaretoken").val());
            }
        }
    });
})(jQuery);

var get_cookie = function (name) {  
    var cookieValue = null;  
    if (document.cookie && document.cookie != '') {  
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }  
    return cookieValue;  
};

var get_size = function (obj){  
    var n, count = 0;
    for(n in obj){
        if(obj.hasOwnProperty(n)){
            count++;
        }
    }  
    return count;  
};

var alert_box = function(title, body) {
    $.messager.alert(title, body);
};

var confirm_box = function(title, body, func) {
    $.messager.confirm(title, body, func);
}

var update_select_options = function($selector, items) {
    if (!$selector.length) {
        return;
    }
    var first_option = $selector.find('option').first().html();
    $selector.empty();
    $selector.append('<option>' + first_option + '</option>');
    if (!items) {
        $selector.selectpicker('refresh');  //clear selector if items is null
        return;
    }
    for(var i=0; i < items.length; i++) {
        var val = items[i][0];
        var display_val = items[i][1];
        var active = items[i][2] ? ' selected' : '';
        var data_str = '';
        for (var data_attr in  val) {
            data_str += 'data-' + data_attr + '="' + val[data_attr] + '" '
        }
        $selector.append("<option " + data_str + active + ">" + (i + 1) + '. ' + display_val + "</option>");
    }
    $selector.selectpicker('refresh');
};

var ajax_error_handler = function (xhr, type, msg) {
    alert_box("Ajax error with Code: " + xhr.status, 'Type: ' + type + ', Msg: ' + msg);
};

var ajax_post_data = function(url, data, success_code) {
    var process_data = true;
    if (typeof data == 'string') {
        process_data = false;
    }
    $.ajax({
            type: "POST",
            url: url,
            processData: process_data,
            data: data,
            timeout: 2000,
            dataType: "json",
            success: function (json) {
                if ('code' in json && 'result' in json) {
                    if (json.code) {
                        alert_box(url + " return error " + json.code, json.result);
                    } else {
                        success_code(json.result);
                    }
                } else {
                    alert_box(url + " return illegal data!", "Receive illegal JSON data: Not found key 'code' or 'result'!");
                }
            },
            error: ajax_error_handler
    });
};

$("select[name='project_name']").change( function() {
    cur_url = window.location.href
    if (cur_url.indexOf('/build') > -1) {
        window.location.href = '/build?prj_id=' + $(this).val()
    } else if (cur_url.indexOf('/testaction') > -1) {
        window.location.href = '/testaction?prj_id=' + $(this).val()
    } else if (cur_url.indexOf('/host') > -1) {
        window.location.href = '/host?prj_id=' + $(this).val()
    } else if (cur_url.indexOf('/testcase') > -1) {
        window.location.href = '/testcase?prj_id=' + $(this).val()
    } else if (cur_url.indexOf('/testresult') > -1) {
        window.location.href = '/testresult?prj_id=' + $(this).val()
    } else if (cur_url.indexOf('/crash') > -1) {
        window.location.href = '/crash?prj_id=' + $(this).val()
    }
});

$("select[name='build_version']").change( function() {
    cur_url = window.location.href
    if (cur_url.indexOf('/build') > -1) {
        window.location.href = '/build?build_id=' + $(this).val();
    } else if (cur_url.indexOf('/host') > -1) {
        build_id = $(this).val();
        if (build_id) {
            window.location.href = '/host?build_id=' + build_id;
        } else {
            prj_id = $("select[name='project_name']").val();
            window.location.href = '/host?prj_id=' + prj_id;
        }
    } else if (cur_url.indexOf('/testcase') > -1) {
        build_id = $(this).val();
        if (build_id) {
            window.location.href = '/testcase?build_id=' + build_id;
        } else {
            prj_id = $("select[name='project_name']").val();
            window.location.href = '/testcase?prj_id=' + prj_id;
        }
    } else if (cur_url.indexOf('/crash') > -1) {
        prj_id = $("select[name='project_name']").val();
        build_id = $(this).val();
        testcase_id = $("select[name='testcase']").val();
        host_id = $("select[name='host']").val();
        if (build_id) {
            window.location.href = '/crash?build_id=' + build_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        } else {
            window.location.href = '/crash?prj_id=' + prj_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        }
    } else if (cur_url.indexOf('/testresult') > -1) {
        prj_id = $("select[name='project_name']").val();
        build_id = $(this).val();
        host_id = $("select[name='host']").val();
        if (build_id) {
            window.location.href = '/testresult?build_id=' + build_id + '&host_id=' + host_id;
        } else {
            window.location.href = '/testresult?prj_id=' + prj_id + '&host_id=' + host_id;
        }
    }
});


$("select[name='host']").change( function() {
    cur_url = window.location.href
    if (cur_url.indexOf('/crash') > -1) {
        prj_id = $("select[name='project_name']").val();
        build_id = $("select[name='build_version']").val();
        testcase_id = $("select[name='testcase']").val();
        host_id = $(this).val();
        if (build_id) {
            window.location.href = '/crash?build_id=' + build_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        } else {
            window.location.href = '/crash?prj_id=' + prj_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        }
    } else if(cur_url.indexOf('/testresult') > -1) {
        prj_id = $("select[name='project_name']").val();
        build_id = $("select[name='build_version']").val();
        host_id = $(this).val();
        if (build_id) {
            window.location.href = '/testresult?build_id=' + build_id + '&host_id=' + host_id;
        } else {
            window.location.href = '/testresult?prj_id=' + prj_id + '&host_id=' + host_id;
        }
    }
});

$("select[name='testcase']").change( function() {
    cur_url = window.location.href
    if (cur_url.indexOf('/crash') > -1) {
        prj_id = $("select[name='project_name']").val();
        build_id = $("select[name='build_version']").val();
        host_id = $("select[name='host']").val();
        testcase_id = $(this).val();
        if (build_id) {
            window.location.href = '/crash?build_id=' + build_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        } else {
            window.location.href = '/crash?prj_id=' + prj_id + '&host_id=' + host_id + '&testcase_id=' + testcase_id;
        }
    }
});


$(function(){
    if (typeof hosts != 'undefined') {
        update_select_options($('select[name="td_host"]'), hosts);
    }
    if (typeof testcases != 'undefined') {
        update_select_options($('select[name="td_testcase"]'), testcases);
    }
    if (typeof projects != 'undefined') {
        update_select_options($('select[name="td_project_name"]'), projects);
    }
    if (typeof builds != 'undefined') {
        update_select_options($('select[name="td_build_version"]'), builds);
    }
});