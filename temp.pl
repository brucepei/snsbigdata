use LWP::UserAgent;
my $ua = LWP::UserAgent->new;
$ua->agent("MyApp/0.1 ");

my $res = $ua->post('http://127.0.0.1/auto/query_build', {
    'project_name' => "MDM9x07.LE.1.1",
});

$res = $ua->post('http://127.0.0.1/auto/crash_info', {
    'project_name' => "MDM9x07.LE.1.1",
    'build_version' => "version001",
    'path' => "\\\\mdm\\c002",
    'host_name' => "SDC-CNSS-031",
    'host_ip' => "1.1.1.1",
    'testcase_name' => "testplan1_s3_s4_traffic",
});


# Check the outcome of the response
if ($res->is_success) {
    print $res->content;
}
else {
    print $res->status_line, "\n";
}
