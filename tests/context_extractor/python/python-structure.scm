; 파일 구조 추출 전용 쿼리
; 모듈 docstring, import 문, 클래스, 함수 정의와 해당하는 docstring을 추출합니다

; 모듈 docstring - 파일 첫 번째 문장의 string 리터럴
(module 
  (expression_statement 
    (string) @module.docstring))

; Import 문들
(import_statement) @import.statement
(import_from_statement) @import.from_statement  
(future_import_statement) @import.future_statement

; 클래스 정의와 docstring
(class_definition 
  name: (identifier) @class.name
  body: (block 
    (expression_statement 
      (string) @class.docstring)?)) @class.definition

; 함수 정의와 docstring
(function_definition 
  name: (identifier) @function.name
  body: (block 
    (expression_statement 
      (string) @function.docstring)?)) @function.definition