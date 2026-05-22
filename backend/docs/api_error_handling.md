# API 错误处理机制文档

## 概述

本文档描述了山海经视频制作全流程留痕系统的统一API错误处理机制，包括自定义异常类、错误响应格式、装饰器工具等。

## 错误响应格式

### 统一响应格式

所有API响应都遵循统一的JSON格式：

#### 成功响应
```json
{
  "success": true,
  "timestamp": "2026-05-22T10:00:00Z",
  "data": {
    // 具体数据内容
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request": {
    "method": "GET",
    "path": "/api/v1/records",
    "query_params": {},
    "user_agent": "Mozilla/5.0..."
  }
}
```

#### 错误响应
```json
{
  "success": false,
  "timestamp": "2026-05-22T10:00:00Z",
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found.",
    "details": {
      "field_errors": {
        "id": "Record 123 not found"
      }
    },
    "request_id": "req_123456789"
  },
  "request": {
    "method": "GET",
    "path": "/api/v1/records/123",
    "query_params": {},
    "user_agent": "Mozilla/5.0..."
  }
}
```

## 自定义异常类

### 基础异常类

```python
from app.exceptions import BaseException

class BaseException(Exception):
    """基础异常类"""
    def __init__(self, message, code="INTERNAL_ERROR", status_code=500, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
```

### 具体异常类

| 异常类 | 状态码 | 错误代码 | 用途 |
|--------|--------|----------|------|
| BadRequestException | 400 | BAD_REQUEST | 请求参数错误 |
| NotFoundException | 404 | NOT_FOUND | 资源不存在 |
| UnauthorizedException | 401 | UNAUTHORIZED | 未授权 |
| ForbiddenException | 403 | FORBIDDEN | 禁止访问 |
| ConflictException | 409 | CONFLICT | 资源冲突 |
| UnprocessableEntityException | 422 | UNPROCESSABLE_ENTITY | 无法处理的实体 |
| ValidationException | 422 | VALIDATION_ERROR | 数据验证错误 |
| DatabaseException | 500 | DATABASE_ERROR | 数据库错误 |
| ExternalServiceException | 502 | EXTERNAL_SERVICE_ERROR | 外部服务错误 |

## 装饰器工具

### 1. api_response 装饰器

统一API响应格式装饰器，自动包装响应数据。

```python
from app.decorators import api_response

@api_response(message="Records retrieved successfully")
@handle_database_errors
def list_records():
    records = Record.query.all()
    return [_serialize_record(r) for r in records]
```

### 2. validate_data 装饰器

数据验证装饰器，自动验证请求数据格式。

```python
from app.decorators import validate_data

@validate_data({
    'required': ['creature_name', 'work_date'],
    'types': {
        'creature_name': 'string',
        'work_date': 'string',
        'plan_id': 'integer',
        'tools_used': 'array'
    }
})
def create_record():
    data = request.get_json()
    # 创建记录逻辑
```

### 3. handle_database_errors 装饰器

数据库错误处理装饰器，自动捕获并转换数据库异常。

```python
from app.decorators import handle_database_errors

@handle_database_errors
def update_record(record_id):
    record = db.session.get(Record, record_id)
    # 更新记录逻辑
```

### 4. log_api_call 装饰器

API调用日志装饰器，自动记录请求和响应信息。

```python
from app.decorators import log_api_call

@log_api_call
def create_record():
    # 创建记录逻辑
```

### 5. require_api_key 装饰器

API密钥验证装饰器，验证请求中的API密钥。

```python
from app.decorators import require_api_key

@require_api_key
def protected_api():
    # 受保护的API逻辑
```

## 使用示例

### 创建记录

#### 旧方式
```python
@records_bp.route("", methods=["POST"])
def create_record():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    creature_name = data.get("creature_name")
    if not creature_name:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "creature_name is required"}}), 400

    # 创建记录...
    return jsonify({"success": True, "data": record_dict}), 201
```

#### 新方式
```python
@records_bp.route("", methods=["POST"])
@api_response(message="Record created successfully")
@validate_data({
    'required': ['creature_name'],
    'types': {
        'creature_name': 'string',
        'plan_id': 'integer',
        'work_date': 'string',
        'tools_used': 'array'
    }
})
@handle_database_errors
def create_record():
    data = request.get_json()
    
    # 创建记录...
    return record_dict  # 自动包装成统一响应格式
```

### 获取记录

#### 旧方式
```python
@records_bp.route("/<int:record_id>", methods=["GET"])
def get_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Record {record_id} not found"}}), 404
    
    return jsonify(_serialize_record(record))
```

#### 新方式
```python
@records_bp.route("/<int:record_id>", methods=["GET"])
@api_response(message="Record retrieved successfully")
@handle_database_errors
def get_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        raise NotFoundException(f"Record {record_id} not found")
    
    return _serialize_record(record)
```

## 错误处理最佳实践

1. **使用自定义异常**：抛出自定义异常而不是直接返回错误响应
2. **统一响应格式**：使用 `@api_response` 装饰器确保响应格式一致
3. **数据验证**：使用 `@validate_data` 装饰器验证请求数据
4. **错误日志**：使用 `@log_api_call` 装饰器记录API调用日志
5. **数据库错误处理**：使用 `@handle_database_errors` 装饰器处理数据库异常

## 错误代码规范

| 错误代码 | 描述 | HTTP状态码 |
|----------|------|------------|
| SUCCESS | 操作成功 | 200 |
| BAD_REQUEST | 请求参数错误 | 400 |
| UNAUTHORIZED | 未授权 | 401 |
| FORBIDDEN | 禁止访问 | 403 |
| NOT_FOUND | 资源不存在 | 404 |
| CONFLICT | 资源冲突 | 409 |
| UNPROCESSABLE_ENTITY | 无法处理的实体 | 422 |
| VALIDATION_ERROR | 数据验证错误 | 422 |
| DATABASE_ERROR | 数据库错误 | 500 |
| EXTERNAL_SERVICE_ERROR | 外部服务错误 | 502 |
| INTERNAL_ERROR | 内部服务器错误 | 500 |

## 测试错误处理

### 测试成功响应
```bash
curl -X GET "http://localhost:5000/api/v1/records"
```

响应示例：
```json
{
  "success": true,
  "timestamp": "2026-05-22T10:00:00Z",
  "data": [...],
  "message": "Records retrieved successfully",
  "code": "SUCCESS",
  "request": {
    "method": "GET",
    "path": "/api/v1/records",
    "query_params": {},
    "user_agent": "curl/7.68.0"
  }
}
```

### 测试错误响应
```bash
curl -X GET "http://localhost:5000/api/v1/records/99999"
```

响应示例：
```json
{
  "success": false,
  "timestamp": "2026-05-22T10:00:00Z",
  "error": {
    "code": "NOT_FOUND",
    "message": "Record 99999 not found",
    "details": {}
  },
  "request": {
    "method": "GET",
    "path": "/api/v1/records/99999",
    "query_params": {},
    "user_agent": "curl/7.68.0"
  }
}
```