
function docker_search(CSRF, URL) {
    var name = $.trim($('#image-name').val());
    if (name.length == 0) {
        alert('待查询的镜像名称不能为空！');
        return false
    };
    $.ajaxSetup({
        data: {
            csrfmiddlewaretoken: CSRF
        }
    });
    $('.push-result').html('<i class="fa fa-spinner fa-pulse fa-3x my-3"></i>');
    $.ajax({
        type: 'post',
        url: URL,
        data: {
            'name': name,
        },
        dataType: 'json',
        success: function(ret) {
            var newhtml = '<table class="table table-bordered my-0"><thead class="thead-light"><tr><th scope="col">镜像版本</th>' +
            '<th scope="col">镜像大小</th><th scope="col">更新时间</th></tr></thead><tbody>';
            for (var i=0;i < ret.results.length; i++) {
                var item = ret.results[i]
                newhtml += '<tr><th scope="row">' + item.name + '</th><td>' + item.full_size + '</td><td>' + item.last_updated + '</td></tr>'
            }
            newhtml += '</tbody></table>'
            $('.push-result').html(newhtml);
        },
        error: function(XMLHttpRequest) {
            var _code = XMLHttpRequest.status;
            if (_code == 404) {
                var error_text = '镜像仓库没有查询到相关信息，请检查镜像名称后重试！';
            } else if (_code == 500) {
                var error_text = '请求超时，请稍后重试！'
            } else {
                var error_text = '未知错误...'
            }
            var newhtml = '<div class="my-2">' + error_text + '</div>';
            $('.push-result').html(newhtml);
        }
    })
}