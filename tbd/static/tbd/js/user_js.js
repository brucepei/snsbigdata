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
    $.ajax({
            type: "POST",
            url: url,
            processData: true,
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
        });
    } else {
        $td_build_version_sel.empty();
        $td_build_version_sel.append("<option>--select build--</option>")
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

$('tr.build_head').click(function(){
    // alert($(this).nextUntil('tr.build_head').length)
    $(this).nextUntil('tr.build_head').toggleClass('hidden');
});