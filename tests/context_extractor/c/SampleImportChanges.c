/**
 * Import 변경 테스트용 샘플 파일 - multiline include 구문 포함
 */

#include <stdio.h>
#include <stdlib.h>

#include <string.h>
#include "custom.h"

#define MAX_BUFFER_SIZE 1024
#define DEFAULT_VALUE 42

#ifdef DEBUG
#define LOG(msg) printf("DEBUG: %s\n", msg)
#else
#define LOG(msg)
#endif

typedef struct {
    char* data;
    int length;
    int capacity;
} ProcessResult;

typedef struct {
    char name[100];
    int value;
} ImportTestStruct;

ProcessResult* process_data(const char* input) {
    /**
     * 데이터 처리 함수
     */
    ProcessResult* result = (ProcessResult*)malloc(sizeof(ProcessResult));
    result->data = (char*)malloc(MAX_BUFFER_SIZE);
    result->length = 0;
    result->capacity = MAX_BUFFER_SIZE;
    
    // 간단한 데이터 복사
    strncpy(result->data, input, MAX_BUFFER_SIZE - 1);
    result->data[MAX_BUFFER_SIZE - 1] = '\0';
    result->length = strlen(result->data);
    
    LOG("Data processed successfully");
    
    return result;
}

void helper_function() {
    /**
     * 도우미 함수
     */
    printf("Helper function called with default value: %d\n", DEFAULT_VALUE);
}

// 모듈 상수
static const char* MODULE_CONSTANT = "test_value";

void cleanup_process_result(ProcessResult* result) {
    if (result) {
        if (result->data) {
            free(result->data);
        }
        free(result);
    }
}