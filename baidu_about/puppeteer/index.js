'use strict';

const oldTime = new Date()
const fs = require('fs')
const puppeteer = require('puppeteer');
const devices = require('puppeteer/DeviceDescriptors');

let keywords = [
    '温州不孕不育医院',
    '温州不孕不育医院哪家好'
]
let ret = {}
let links = {}

let save = function (filename, data) {
    return new Promise(function (resolve, reject) {
        fs.writeFile(filename, data, error => {
            if (error) return reject(error)
            resolve('saved')
        })
    })
};


(async () => {
    const browser = await puppeteer.launch()
    for (let keyword of keywords) {
        ret[keyword] = {}
        const page = await browser.newPage()
        await page.emulate(devices['iPhone 6'])
        await page.goto(`https://m.baidu.com/s?word=${keyword}`, {waitUntil: 'networkidle'})
        links[keyword] = await page.evaluate(() => {
            const anchors = Array.from(document.querySelectorAll('#page-relative .rw-list .rw-item'))
            return anchors.map(anchor => anchor.textContent)
        })
        await page.close()
    }
    // for (let link in links) {
    //     for (let item of links[link]) {
    //         const page = await browser.newPage()
    //         await page.emulate(devices['iPhone 6'])
    //         await page.goto(item.url, {waitUntil: 'networkidle'})
    //         ret[link][item.title] = await page.evaluate(() => {
    //             const anchors = Array.from(document.querySelectorAll('#page-relative .rw-list .rw-item'))
    //             return anchors.map(anchor => anchor.textContent)
    //         })
    //         await page.close()
    //     }
    // }
    await browser.close()
    await save('data.json', JSON.stringify(links, null, 4))
    console.log((new Date()).getTime() - oldTime.getTime())
})()
