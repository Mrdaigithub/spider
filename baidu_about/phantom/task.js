"use strict";

var page = require('webpage').create()
var system = require('system')

var keyword = system.args[1]
var url = encodeURI('https://m.baidu.com/s?word=' + keyword)

phantom.outputEncoding = 'utf8'
page.settings.userAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1page.settings.userAgent = theDevice['userAgent']"
page.settings.viewportSize = {
    width: '375',
    height: '667'
}
page.clipRect = {
    top: 0,
    left: 0,
    width: '375',
    height: '667'
}

page.open(url, function (s) {
    if (s === 'success') {
        var dataList = page.evaluate(function () {
            var dataList = []
            $('#page-relative .rw-list .rw-item').each(function (index) {
                dataList.push($(this).text())
            })
            return dataList
        })
    }
    console.log(JSON.stringify(dataList))
    phantom.exit()
})
