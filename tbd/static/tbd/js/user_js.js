$("select[name]").filter("[name='project_name'],[name='build_version']").change( function() {
    cur_url = window.location.href
    if (cur_url.indexOf('/build') > -1) {
        if ($(this).val().indexOf('--') != 0) {
            window.location.href = '/build?project_name=' + $(this).val()
        }
    }
    else if(cur_url.indexOf('/testdata')) {
        if ($(this).val().indexOf('--') != 0) {
            window.location.href = '/testdata?project_name=' + $(this).val()
        }
    }
});


$('tr.build_head').click(function(){
    // alert($(this).nextUntil('tr.build_head').length)
    $(this).nextUntil('tr.build_head').toggleClass('hidden');
});