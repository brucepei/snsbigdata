(function($) {
    $.fn.getAttributes = function() {
        var attributes = {}; 
        if( this.length ) {
            $.each( this[0].attributes, function( index, attr ) {
                attributes[ attr.name ] = attr.value;
            } ); 
        }
        return attributes;
    };
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

var alert_box = function(title, body) {
    $.messager.alert(title, body);
};

var confirm_box = function(title, body, func) {
    $.messager.confirm(title, body, func);
}

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
            beforeSend: function(xhr, settings){  
                xhr.setRequestHeader("X-CSRFToken", get_cookie('csrftoken'));  
            },
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
        if ($(this).val().indexOf('--') != 0) {
            window.location.href = '/build?project_name=' + $(this).val()
        }
    }
});

$("select[name='td_project_name']").change( function() {
    var $td_build_version_sel = $("select[name='td_build_version']");
    var get_build_url = '/ajax_get_builds'
    var prj_name = $(this).val();
    if (prj_name.indexOf('--') != 0) {
        ajax_post_data(get_build_url, {'project_name': prj_name}, function(builds){
            $td_build_version_sel.empty();
            $td_build_version_sel.append("<option>--select build--</option>")
            for(var i=0; i < builds.length; i++) {
                $td_build_version_sel.append("<option value='"+builds[i]+"'>" + (i + 1) + '. ' +builds[i]+"</option>");
            }
            $td_build_version_sel.selectpicker('refresh');
        });
    } else {
        $td_build_version_sel.empty();
        $td_build_version_sel.append("<option>--select build--</option>")
        $td_build_version_sel.selectpicker('refresh');
    }
});

$("select[name='td_build_version']").change( function() {
    var prj_name = $("select[name='td_project_name']").val();
    var build_version = $(this).val();
    cur_url = window.location.href;
    if(cur_url.indexOf('/testdata')) {
        if (build_version.indexOf('--') != 0) {
            window.location.href = '/testdata?project_name=' + prj_name + "&version=" + build_version;
        }
    }
});

$('button.add_btn').click(function(){
    if ($(this).html() == 'Add') {
        var $add_sel = $(this).parent().find("select");
        var $inputs = $(this).closest('tr').nextUntil('tr.crash_head').find('input, select');
        var is_input_empty = true;
        $inputs.each(function(){
            if ($(this).attr('type') != 'hidden' && $(this).val()) {
                is_input_empty = false;
                return false;
            }
            return true;
        });
        if (is_input_empty) {
            $(this).closest('tr').nextUntil('tr.crash_head').toggleClass('hidden');
            $(this).html('Extend');
            $(this).removeClass('btn btn-primary');
            $(this).addClass('btn btn-default');
            return;
        }
        var data_content = $inputs.serialize();
        var url = $(this).attr('action');
        var $add_btn = $(this);
        if (url) {
            ajax_post_data(url, data_content, function(items){
                var first_option = $add_sel.find('option').first().html();
                $add_sel.empty();
                $add_sel.append('<option>' + first_option + '</option>')
                for(var i=0; i < items.length; i++) {
                    var val = items[i][0];
                    var display_val = items[i][1];
                    var active = items[i][2] ? ' selected' : '';
                    var data_str = '';
                    for (var data_attr in  val) {
                        data_str += 'data-' + data_attr + '="' + val[data_attr] + '" '
                    }
                    $add_sel.append("<option " + data_str + active + ">" + (i + 1) + '. ' + display_val + "</option>");
                }
                $add_sel.selectpicker('refresh');
                $inputs.each(function(){
                    if ($(this).attr('type') != 'hidden' && $(this).val()) {
                        $(this).val('');
                        $(this).selectpicker('refresh');
                    }
                    return true;
                });
                $add_btn.closest('tr').nextUntil('tr.crash_head').toggleClass('hidden');
                $add_btn.html('Extend');
                $add_btn.removeClass('btn btn-primary');
                $add_btn.addClass('btn btn-default');
                var $pop_element = $add_btn.siblings('div.bootstrap-select');
                $pop_element.popover({'placement': 'top', 'content': 'add successfully!'});
                $pop_element.popover('show');
                $pop_element.one('click', function(){
                    $pop_element.popover('destroy');
                });
            });
        } else {
            alert_box("Unknown Action", "Not found URL in action attribute!");
        }
    } else {
        $(this).html('Add');
        $(this).removeClass('btn btn-default');
        $(this).addClass('btn btn-primary');
        $(this).closest('tr').nextUntil('tr.crash_head').toggleClass('hidden');
    }
});

$('button.del_btn').click(function(){
    var url = $(this).attr('action');
    var $select = $(this).parent().find("select");
    var $del_option = $select.find("option:selected");
    var del_attrs = $del_option.getAttributes();
    var data_attrs = {};
    var data_count = 0;
    var all_attrs = $del_option.getAttributes();
    var $inputs = $(this).closest('tr').nextUntil('tr.crash_head').find('input[type="hidden"]');
    $inputs.each(function(){
        data_attrs[$(this).attr('name')] = $(this).val();
    });
    for (attr_name in all_attrs) {
        if (attr_name.indexOf("data-") == 0) {
            data_attrs[attr_name.substr(5)] = all_attrs[attr_name];
            data_count++;
        }
    }
    if (url) {
        if (data_count) {
            confirm_box("Delete?", "Do you confirm you really want to delete it?", function() {
                ajax_post_data(url, data_attrs, function(items){
                    //alert_box('Delete', "done!");
                    var first_option = $select.find('option').first().html();
                    $select.empty();
                    $select.append('<option>' + first_option + '</option>')
                    for(var i=0; i < items.length; i++) {
                        var val = items[i][0];
                        var active = items[i][1] ? ' selected' : '';
                        $select.append("<option data-host_name='"+val.name+"' data-host_ip='" + val.ip + "' data-host_mac='" + val.mac + "'" + active + ">" + (i + 1) + '. ' + val.name + "(" + val.ip +")</option>");
                    }
                    $select.selectpicker('refresh');
                });
            });
        } else {
            alert_box("Not select", "Not select any target!");
        }
    } else {
        alert_box("Unknown Action", "Not found URL in action attribute!");
    }
});

$('a>span.glyphicon-remove').click(function(){
    var goto_url = $(this).parent().attr('href');
    confirm_box("Delete?", "Do you confirm you really want to delete it?", function() {
        window.location.href = goto_url;
    });
    return false;
});

$('tr.build_head').click(function(){
    // alert($(this).nextUntil('tr.build_head').length)
    $(this).nextUntil('tr.build_head').toggleClass('hidden');
});