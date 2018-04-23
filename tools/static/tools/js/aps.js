console.log("test aps.js");
app.run(['editableOptions', '$rootScope', function(editableOptions, $rootScope) {
    editableOptions.theme = 'bs3'; // bootstrap3 theme. Can be also 'bs2', 'default'
}]);
app.controller('SelectLocalCtrl', function($scope, $filter, $http, $log, $location) {
    $scope.owners = [
        {text: "Owner: All", value: ''},
        {text: "Owner: for_sdm845", value: 'for_sdm845'},
        {text: "Owner: for_apq", value: 'for_apq'},
    ];
    $scope.filterOwner = {text: "Owner: for_sdm845", value: 'for_sdm845'};
    $scope.$watch('filterOwner.value', function(newVal, oldVal) {
        if (newVal !== oldVal) {
            var selected = $filter('filter')($scope.owners, {value: $scope.filterOwner.value});
            if (selected.length) {
                $scope.filterOwner.text = selected[0].text;
                $scope.filterOwner.value = selected[0].value;
                $scope.$parent.filterAp = $scope.filterOwner.value;

                $location.search('filter', $scope.$parent.filterAp);
                $log.debug("set url=" + $location.url());
            }
            console.log("filter owner changed to: " + $scope.filterOwner.value);
        }
    });
});
app.controller('EditableRowCtrl', function($scope, $filter, $http, $location, $log) {
    var query_args = $location.search();
    $scope.isDefined = angular.isDefined;
    if (query_args.filter) {
        $scope.filterAp = query_args.filter;
        $log.debug("set filter AP from url: " + $scope.filterAp);
    } else {
        $scope.filterAp = "";
        $log.debug("set filter AP to empty");
    }
    $http.get('/tools/ap_list').then(function(resp) {
        var ap_data = resp.data;
        if (ap_data) {
            $log.debug(ap_data);
            $scope.aps = ap_data;
        } else {
            $log.debug("Cannot get ap data from remote!")
        }
    });
    // $scope.aps = [
    //     {id: 1, brand: 'Cisco', ssid: 'sns-test-2g', type: 'WEP', password: '1234567890', owner: 'for_sdm845', aging: '15 mins'},
    //     {id: 2, brand: 'Cisco', ssid: 'sns-test-5g', type: 'WPA2', password: '1234567890', owner: 'for_apq', aging: '25 mins'},
    // ];
    $scope.types = [];
    $scope.loadTypes = function() {
        return $scope.types.length ? null : $http.get('/tools/api/ap_types').then(function(data) {
            for (var i =0; i < data.data.length; i++) {
                data.data[i] = {value: data.data[i][0], text: data.data[i][1]};
            };
            $scope.types = data.data;
        });
    };

    $scope.showType = function(ap) {
        if(ap.type && $scope.types.length) {
            var selected = $filter('filter')($scope.types, {value: ap.type});
            return selected.length ? selected[0].text : 'Not set';
        } else {
            return ap.type || 'Not set';
        }
    };

    $scope.checkSsid = function(data, id) {
        if (data.length <= 0) {
            return "ssid should not be empty!";
        }
    };

    $scope.checkBrand = function(data, id) {
        console.log("Brand is " + data);
    };

    $scope.checkPassword = function(data, ap) {
        console.log($scope.aps);
        if (ap.type != "OPEN" && data && data.length < 8) {
            return "password of Non-OPEN should be more than 8 chars!";
        } else if (ap.type == "OPEN" && data && data.length != 0) {
            return "password of OPEN should be empty!";
        }
    };

    $scope.checkOwner = function(data, id) {
        console.log("Owner is " + data);
    };

    $scope.saveAp = function(data, id) {
        //$scope.user not updated yet
        angular.extend(data, {id: id});
        return $http.post('/saveAp', data);
    };

    // remove user
    $scope.removeAp = function(index) {
        $scope.aps.splice(index, 1);
    };

    // add user
    $scope.addAp = function() {
        $scope.inserted = {
            id: $scope.aps.length+1,
            brand: '',
            ssid: '',
            type: null,
            password: '',
            owner: '',
            aging: ''
        };
        $scope.aps.push($scope.inserted);
    };
});
