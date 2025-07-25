; 클래스 구조 추출 전용 쿼리
; 클래스와 함수 정의, 그리고 해당하는 docstring을 추출합니다

(class_definition 
  name: (identifier) @class.name
  body: (block 
    (expression_statement 
      (string) @class.docstring)?)) @class.definition

(function_definition 
  name: (identifier) @function.name
  body: (block 
    (expression_statement 
      (string) @function.docstring)?)) @function.definition