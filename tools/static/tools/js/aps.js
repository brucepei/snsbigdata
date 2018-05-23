console.log("test aps.js");
app.run(['editableOptions', '$rootScope', function(editableOptions, $rootScope) {
    editableOptions.theme = 'bs3'; // bootstrap3 theme. Can be also 'bs2', 'default'
    $rootScope.$on('getFilterEvent', function (event, args) {
        $rootScope.$broadcast('applyFilterEvent', args);
    });
}]);
app.controller('SelectLocalCtrl', function($scope, $filter, $http, $log, $location) {
    // $scope.owners = [
        // {text: "Owner: All", value: ''},
        // {text: "Owner: for_sdm845", value: 'for_sdm845'},
        // {text: "Owner: for_apq", value: 'for_apq'},
    // ];
    $scope.$on('applyFilterEvent', function (event, args) {
        $scope.owners = args.options;
        $scope.filterOwner = {text: "Owner: " + args.selected, value: args.selected}
    });
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
    var IP_Regex = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
    var query_args = $location.search();
    $scope.isNumber = angular.isNumber;
    if (query_args.filter) {
        $scope.filterAp = query_args.filter;
        $log.debug("set filter AP from url: " + $scope.filterAp);
    } else {
        $scope.filterAp = "";
        $log.debug("set filter AP to empty");
    }
    $http.get('/tools/api/ap/').then(function(resp) {
        var ap_data = resp.data;
        var owners = [{text: "Owner: All", value: ''}];
        if (ap_data) {
            $log.debug(ap_data);
            $scope.aps = ap_data;
            angular.forEach(ap_data, function(ap, index, array) {
                for (var i=0; i < owners.length; i++) {
                    if (owners[i].value == ap.owner) {
                        return;
                    }
                }
                owners.push({text: "Owner: " + ap.owner, value: ap.owner});
            });
            console.log("Got owners:");
            console.log(owners);
            $scope.$emit('getFilterEvent', {'selected': $scope.filterAp, 'options': owners});
        } else {
            $log.debug("Cannot get ap data from remote!")
        }
    });
    $scope.types = [];
    $scope.loadTypes = function() {
        return $scope.types.length ? null : $http.get('/tools/api/ap/types/').then(function(data) {
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
            return "ssid is must!";
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

    $scope.checkIp = function(data) {
        if (data && !IP_Regex.test(data)) {
            return "Invalid IP address!";
        }
    };

    $scope.checkOwner = function(data, id) {
        console.log("Owner is " + data);
        if (!data) {
            return "Owner is must!";
        }
    };

    $scope.saveAp = function(data, id) {
        angular.extend(data, {id: id});
        console.log("save ap:");
        console.log(data);
        return $http.post('/tools/api/ap', {data: data, method: 'save'}).then(function(resp) {
            console.log("create ap ok!");
            console.log(resp.data);
            if (id == -1) {
                for (var i=0; i < $scope.aps.length; i++) {
                    if ($scope.aps[i].id == -1) {
                        $scope.aps[i].id = resp.data.id;
                        console.log("correct id to " + $scope.aps[i].id);
                        break;
                    }
                }
            }
            return;
        },
        function(resp) {
            console.log(resp);
            return "error";
        });
    };

    // remove user
    $scope.removeAp = function(index, id) {
        return $http.delete('/tools/api/ap/' + id + '/').then(function(resp) {
            console.log("delete ap ok!");
            $scope.aps.splice(index, 1);
            return;
        },
        function(resp) {
            console.log(resp);
            return "error";
        });
    };

    // add user
    $scope.addAp = function() {
        $scope.inserted = {
            id: -1,
            brand: '',
            ssid: '',
            type: null,
            password: '',
            owner: '',
            aging: -1
        };
        $scope.aps.push($scope.inserted);
    };
});
