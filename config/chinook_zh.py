schema_descriptions = {
    "Album": {
        "description": "唱片专辑表，存储专辑的标题和对应的歌手ID",
        "columns": {
            "AlbumId": "专辑唯一标识符，主键",
            "Title": "专辑标题",
            "ArtistId": "关联的歌手/艺术家ID，外键"
        }
    },
    "Artist": {
        "description": "歌手/艺术家表，存储歌手的基本信息",
        "columns": {
            "ArtistId": "歌手唯一标识符，主键",
            "Name": "歌手或乐队的名称"
        }
    },
    "Customer": {
        "description": "客户表，存储购买音乐的客户详细信息",
        "columns": {
            "CustomerId": "客户唯一标识符，主键",
            "FirstName": "客户名",
            "LastName": "客户姓",
            "Company": "客户所属公司",
            "Address": "地址",
            "City": "城市",
            "State": "州/省",
            "Country": "国家",
            "PostalCode": "邮政编码",
            "Phone": "电话号码",
            "Fax": "传真号码",
            "Email": "电子邮件地址",
            "SupportRepId": "负责该客户的销售代表ID，外键关联 Employee 表"
        }
    },
    "Employee": {
        "description": "员工表，存储公司员工的详细信息和汇报关系",
        "columns": {
            "EmployeeId": "员工唯一标识符，主键",
            "LastName": "员工姓",
            "FirstName": "员工名",
            "Title": "职位头衔",
            "ReportsTo": "汇报对象ID，指向另一位员工（经理）",
            "BirthDate": "出生日期",
            "HireDate": "入职日期",
            "Address": "家庭地址",
            "City": "城市",
            "State": "州/省",
            "Country": "国家",
            "PostalCode": "邮政编码",
            "Phone": "电话",
            "Fax": "传真",
            "Email": "工作邮箱"
        }
    },
    "Genre": {
        "description": "音乐流派表，如摇滚、爵士、金属等",
        "columns": {
            "GenreId": "流派唯一标识符，主键",
            "Name": "流派名称"
        }
    },
    "Invoice": {
        "description": "发票/订单表，记录交易的头部信息",
        "columns": {
            "InvoiceId": "发票唯一标识符，主键",
            "CustomerId": "客户ID，外键",
            "InvoiceDate": "发票日期",
            "BillingAddress": "账单地址",
            "BillingCity": "账单城市",
            "BillingState": "账单州/省",
            "BillingCountry": "账单国家",
            "BillingPostalCode": "账单邮编",
            "Total": "发票总金额"
        }
    },
    "InvoiceLine": {
        "description": "发票明细表，记录发票中包含的具体商品",
        "columns": {
            "InvoiceLineId": "明细行唯一标识符，主键",
            "InvoiceId": "所属发票ID，外键",
            "TrackId": "购买的曲目ID，外键",
            "UnitPrice": "单价",
            "Quantity": "数量"
        }
    },
    "MediaType": {
        "description": "媒体类型表，如 MPEG 音频文件、AAC 音频文件等",
        "columns": {
            "MediaTypeId": "媒体类型ID，主键",
            "Name": "媒体类型名称"
        }
    },
    "Playlist": {
        "description": "播放列表表，存储用户创建的播放列表",
        "columns": {
            "PlaylistId": "播放列表ID，主键",
            "Name": "播放列表名称"
        }
    },
    "PlaylistTrack": {
        "description": "播放列表与曲目的关联表（多对多关系）",
        "columns": {
            "PlaylistId": "播放列表ID",
            "TrackId": "曲目ID"
        }
    },
    "Track": {
        "description": "曲目表，存储每首歌曲的详细信息",
        "columns": {
            "TrackId": "曲目唯一标识符，主键",
            "Name": "曲目名称",
            "AlbumId": "所属专辑ID，外键",
            "MediaTypeId": "媒体类型ID，外键",
            "GenreId": "流派ID，外键",
            "Composer": "作曲家",
            "Milliseconds": "时长（毫秒）",
            "Bytes": "文件大小（字节）",
            "UnitPrice": "单价"
        }
    }
}
