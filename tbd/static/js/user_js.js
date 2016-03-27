$("select[name='project_name']").change( function() {
    window.location.href = '/build?project_name=' + $(this).val()
});

$('tr.build_head').click(function(){
    // alert($(this).nextUntil('tr.build_head').length)
    $(this).nextUntil('tr.build_head').toggleClass('hidden');
});