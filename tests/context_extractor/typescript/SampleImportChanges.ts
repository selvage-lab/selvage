/**
 * Import 변경 테스트용 샘플 파일 - multiline import 구문 포함
 */

import * as fs from 'fs';
import { readFile, writeFile } from 'fs/promises';

import path from 'path';
import type { Stats } from 'fs';

interface ProcessResult {
    numbers: string[];
    filePath: string;
    stats?: Stats;
}

class ImportTestClass {
    /**
     * Import 변경 테스트를 위한 클래스
     */
    
    private name: string = '';
    private value: number = 0;
    
    public processData(data: string): ProcessResult {
        /**
         * 데이터 처리 메서드
         */
        const numbers: string[] = [];
        // 간단한 숫자 추출 로직
        for (const c of data) {
            if (!isNaN(Number(c))) {
                numbers.push(c);
            }
        }
        
        const filePath: string = path.join(__dirname, 'test.txt');
        return {
            numbers,
            filePath
        };
    }
}

class HelperClass {
    /**
     * 도우미 클래스
     */
    
    public static helperMethod(): string {
        return 'Helper result';
    }
}

// 모듈 상수
const MODULE_CONSTANT: string = 'test_value';

export { ImportTestClass, HelperClass, MODULE_CONSTANT };
export type { ProcessResult };