**This documentation is automatically generated.**

**Output schemas only represent `data` and not the full output; see output examples and the JSend specification.**

# /api/challenge/?

    Content-Type: application/json

## GET


**Input Schema**
```json
null
```



**Output Schema**
```json
{
    "properties": {
        "levels": {
            "type": "array"
        },
        "lives": {
            "type": "integer"
        },
        "nextLife": {
            "type": "integer"
        },
        "status": {
            "type": "string"
        }
    },
    "type": "object"
}
```


**Output Example**
```json
{
    "levels": [
        {
            "locked": false,
            "name": "easy"
        },
        {
            "locked": false,
            "name": "medium"
        },
        {
            "locked": false,
            "name": "hard"
        },
        {
            "locked": true,
            "name": "impossible"
        }
    ],
    "lives": 3,
    "nextLife": 1474044575,
    "status": "success"
}
```




<br>
<br>

# /api/challengeapi/?

    Content-Type: application/json



<br>
<br>

# /api/game/\(?P\<level\>\[a\-zA\-Z0\-9\_\\\-\]\+\)/?$

    Content-Type: application/json

## GET


**Input Schema**
```json
null
```



**Output Schema**
```json
{
    "properties": {
        "icons": {
            "type": "array"
        },
        "lives": {
            "type": "integer"
        },
        "message": {
            "type": "string"
        },
        "nextLife": {
            "type": "string"
        },
        "status": {
            "type": "string"
        }
    },
    "type": "object"
}
```


**Output Example**
```json
{
    "icons": [
        {
            "code": "eb",
            "key": "ico1"
        },
        {
            "code": "P8",
            "key": "ico2"
        },
        {
            "code": "RB",
            "key": "ico3"
        },
        {
            "code": "nK",
            "key": "ico4"
        },
        {
            "code": "oz",
            "key": "ico5"
        },
        {
            "code": "Aq",
            "key": "ico6"
        },
        {
            "code": "N3",
            "key": "ico7"
        },
        {
            "code": "re",
            "key": "ico8"
        },
        {
            "code": "y5",
            "key": "ico9"
        },
        {
            "code": "p5",
            "key": "ico10"
        },
        {
            "code": "9K",
            "key": "ico11"
        },
        {
            "code": "0V",
            "key": "ico12"
        }
    ],
    "lives": 3,
    "message": "",
    "nextLife": 150,
    "status": "success"
}
```




## POST


**Input Schema**
```json
{
    "properties": {
        "sequence": {
            "type": "string"
        }
    },
    "required": [
        "sequence"
    ],
    "type": "object"
}
```


**Input Example**
```json
{
    "sequence": "a1|b2|c3"
}
```


**Output Schema**
```json
{
    "properties": {
        "lives": {
            "type": "integer"
        },
        "message": {
            "type": "string"
        },
        "nextLife": {
            "type": "string"
        },
        "status": {
            "type": "string"
        },
        "win": {
            "type": "boolean"
        }
    },
    "type": "object"
}
```


**Output Example**
```json
{
    "lives": 1,
    "message": "Not this time.",
    "nextLife": 150,
    "status": "success",
    "win": false
}
```




<br>
<br>

# /api/user/?

    Content-Type: application/json

## GET


**Input Schema**
```json
null
```



**Output Schema**
```json
{
    "properties": {
        "address": {
            "type": "string"
        },
        "astate": {
            "type": "string"
        },
        "city": {
            "type": "string"
        },
        "email": {
            "type": "string"
        },
        "lives": {
            "type": "integer"
        },
        "missing": {
            "type": "object"
        },
        "name": {
            "type": "string"
        },
        "nextLife": {
            "type": "string"
        },
        "status": {
            "type": "string"
        }
    },
    "type": "object"
}
```


**Output Example**
```json
{
    "address": "rua das couves 32",
    "astate": "sp",
    "city": "sao paulo",
    "email": "asd@asd.com",
    "lives": 3,
    "missing": {
        "gamelevel": "easy"
    },
    "name": "Next Gamer 1",
    "nextLife": 1150,
    "status": "success"
}
```




## POST


**Input Schema**
```json
{
    "properties": {
        "address": {
            "minLength": 5,
            "type": "string"
        },
        "astate": {
            "maxLength": 2,
            "minLength": 2,
            "type": "string"
        },
        "city": {
            "minLength": 2,
            "type": "string"
        },
        "email": {
            "format": "email",
            "minLength": 6,
            "type": "string"
        },
        "optin": {
            "type": "boolean"
        }
    },
    "required": [
        "astate",
        "city",
        "address",
        "email",
        "optin"
    ],
    "type": "object"
}
```


**Input Example**
```json
{
    "address": "Rua das couves",
    "astate": "SP",
    "city": "Sao Paulo",
    "email": "rga@rga.com.br",
    "optin": true
}
```


**Output Schema**
```json
{
    "properties": {
        "lives": {
            "type": "integer"
        },
        "message": {
            "type": "string"
        },
        "nextLife": {
            "type": "string"
        },
        "status": {
            "type": "string"
        }
    },
    "type": "object"
}
```


**Output Example**
```json
{
    "lives": 1,
    "message": "",
    "nextLife": 150,
    "status": "success"
}
```



