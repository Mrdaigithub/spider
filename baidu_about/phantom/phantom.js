"use strict";

const http = require('http')
const url = require('url')
const fs = require('fs')
const child_process = require('child_process')

const keywords = [
    '温州做人流'
]

const save = function (filename = 'data.json', data) {
    return new Promise(function (resolve, reject) {
        fs.writeFile(filename, data, error => {
            if (error) return reject(error)
            resolve('saved')
        })
    })
};

const task = function (keyword) {
    return new Promise(function (resolve, reject) {
        child_process.exec(`phantomjs.exe ./task.js ${keyword}`, (err, stdout, stderr) => {
            if (err) return reject(err)
            if (stderr) return reject(`stderr: ${stderr}`)
            resolve(stdout)
        })
    })
};

(async function () {
    let data = {}
    for (let keyword of keywords) {
        data[keyword] = JSON.parse(await task(keyword))
    }
    await save('data.json', JSON.stringify(data, null, 4))
})()
