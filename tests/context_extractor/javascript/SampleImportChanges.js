/**
 * Import 변경 테스트용 샘플 파일 - multiline import 구문 포함
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

import { readFile, writeFile } from 'fs/promises';
import { basename, dirname } from 'path';
import axios from 'axios';

class ImportTestClass {
    /**
     * Import 변경 테스트를 위한 클래스
     */
    
    constructor() {
        this.name = '';
        this.value = 0;
    }
    
    processData(data) {
        /**
         * 데이터 처리 메서드
         */
        const numbers = [];
        // 간단한 숫자 추출 로직
        for (const c of data) {
            if (!isNaN(c)) {
                numbers.push(c);
            }
        }
        
        const filePath = path.join(__dirname, 'test.txt');
        return `Processed: ${numbers}, Path: ${filePath}`;
    }
}

class HelperClass {
    /**
     * 도우미 클래스
     */
    
    static helperMethod() {
        return 'Helper result';
    }
}

// 모듈 상수
const MODULE_CONSTANT = 'test_value';

module.exports = { ImportTestClass, HelperClass, MODULE_CONSTANT };