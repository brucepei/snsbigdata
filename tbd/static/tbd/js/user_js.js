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

var ajax_error_handler = function (xhr, type, msg) {
    alert( 'Ajax error! Code: ' + xhr.status + ', type: ' + type + ', msg: ' + msg );
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
                        alert("Receive JSON error code " + json.code + " with message: " + json.result);
                    } else {
                        success_code(json.result);
                    }
                    
                } else {
                    alert("Receive illegal JSON data: Not found key 'code' or 'result'!");
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

$('button.adjust_btn').click(function(){
    if ($(this).html() == 'Hidden') {
        $(this).html('Extend');
        $(this).removeClass('btn btn-primary');
        $(this).addClass('btn btn-default');
    } else {
        $(this).html('Hidden');
        $(this).removeClass('btn btn-default');
        $(this).addClass('btn btn-primary');
    }
    $(this).nextAll().toggleClass('hidden');
    $(this).closest('tr').nextUntil('tr.crash_head').toggleClass('hidden');
});

$('button.add_btn').click(function(){
    var $add_sel = $(this).parent().find("select");
    var $inputs = $(this).closest('tr').nextUntil('tr.crash_head').find('input, select');
    var data_content = $inputs.serialize();
    var url = $(this).attr('action');
    if (url) {
        ajax_post_data(url, data_content, function(items){
            var first_option = $add_sel.find('option').first().html();
            $add_sel.empty();
            $add_sel.append('<option>' + first_option + '</option>')
            for(var i=0; i < items.length; i++) {
                $add_sel.append("<option value='"+items[i]+"'>" + (i + 1) + '. ' +items[i]+"</option>");
            }
            $add_sel.selectpicker('refresh');
        });
    } else {
        alert("Not found URL in action attribute!");
    }
});

$('tr.build_head').click(function(){
    // alert($(this).nextUntil('tr.build_head').length)
    $(this).nextUntil('tr.build_head').toggleClass('hidden');
});