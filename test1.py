def Avatar_execute(num,fundata):
    print('传进子线成的数据',fundata)
    print('子线程1：', num.value)

    #加载环境才能拿到包
    try:
        print('开始加载环境')
        sys.path.append(r"stablediffusionwebui15")
        import webui2 as core
        core.initialize()
        print('加载环境完成')
        # raise Exception("抛出自定义异常")
    except Exception as e:
        savejson_util.errormodel_json(num,code=500,msg='加载环境异常：'+str(e),taskId=fundata["taskId"])
        

    #sd模型
    from modules.sd_models import checkpoints_list, unload_model_weights, reload_model_weights, checkpoint_aliases
    from modules.sd_models_config import find_checkpoint_config_near_filename
    
    try: 
        #初始化已经刷新
        sdreq=[{"title": x.title, "model_name": x.model_name, "hash": x.shorthash, "sha256": x.sha256, "filename": x.filename, "config": find_checkpoint_config_near_filename(x)} for x in checkpoints_list.values()]
        # raise Exception("抛出自定义异常")
        for value in sdreq:
            print('SD名称：',value['model_name'],value['title'])
        if not fundata['styleName'] in str(sdreq): #判断模型是否存在
            savejson_util.errormodel_json(num,code=400,msg='SDbase模型名称错误',taskId=fundata["taskId"])
        
    except Exception as e:
        savejson_util.errormodel_json(num,code=500,msg='SD模型获取异常'+str(e),taskId=fundata["taskId"])
       
    #Lora模型
    sys.path.append(r'stablediffusionwebui15/extensions-builtin/Lora/')
    import networks23 #文件同名冲突，更改
    from scripts.lora_script import create_lora_json

    try: 
        #刷新Lora，不加载环境要刷新
        lorareq=networks23.list_available_networks()
        print('刷新lorareq值：',lorareq)
        # raise Exception("抛出自定义异常")

        #获取Lora
        lorareq2=[create_lora_json(obj) for obj in networks23.available_networks.values()]
        # print('lorareq2值：',lorareq2)
        if not fundata['userModelId'] in str(lorareq2): #判断模型是否存在
            savejson_util.errormodel_json(num,code=400,msg='Lora模型名称错误',taskId=fundata["taskId"])
        for value in lorareq2:
            print('Lora名称：',value['name'],value['alias'])             

    except Exception as e:
        savejson_util.errormodel_json(num,code=500,msg='Lora模型获取异常'+str(e),taskId=fundata["taskId"])
       


    #2、文生图，生成用户图片，结合lora、controlnet
  
    from PIL import Image
    try:
        # 对promt进行处理
        config['txt2img_data']['override_settings']['sd_model_checkpoint']=fundata['styleName']
        config['txt2img_data']['prompt']=config['txt2img_data']['prompt']+f'<lora:{fundata["userModelId"]}:1>'
        # if fundata['seed']: #查看种子是否为空,设置生成图片数量
        #     config['txt2img_data']['seed']=fundata['seed']
        #     config['txt2img_data']['batch_size']=1
         
        # else:
        #     config['txt2img_data']['seed']=-1
        #     config['txt2img_data']['batch_size']=5

        # 文生图，结合lora、controlnet
        respon=core.api_only(config['txt2img_data'])
        if not respon or not respon['info']:
            savejson_util.errormodel_json(num,code=500,msg='文生图数据为空',taskId=fundata["taskId"])
          
        req_into=json.loads(respon['info'])
        print('文生图信息',req_into)       
    except Exception as e:
        savejson_util.errormodel_json(num,code=500,msg='文生图出现异常'+str(e),taskId=fundata["taskId"])


       
    #3、上传图片，成功保存数据
    try:
         #封装上传图片
        import datetime
        cur_time=datetime.datetime.now().strftime('%Y%m%d%H%M%S_%f')
        print('cur_time:',cur_time)
        local_dir=f'./data/imgdata/imgs/{fundata["taskId"]}' #测试用，可注释
        remote_dir=f'mnt/tmp/data/userimgs/{fundata["userId"]}/Avatar/{cur_time}' #加Avatar
        dirs_util.del_dirs(local_dir)  #测试用，可注释 
        dirs_util.del_dirs(remote_dir) 
        
        img_data=[]
        for imgvalu,seed in zip(respon['images'],req_into['all_seeds']):
            image = Image.open(io.BytesIO(base64.b64decode(imgvalu.split(",", 1)[0])))
            image.save(f'{local_dir}/{seed}.png') #测试用，可注释
            image.save(f'{remote_dir}/{seed}.png')
            per_seed = {'imgUrl': f'{remote_dir}/{str(seed)}.png', 'seed': seed}
            img_data.append(per_seed)
        savejson_util.errormodel_json(num,code=200,msg='图片生成成功',taskId=fundata["taskId"],imageSeeds=img_data)
    except Exception as e:
        savejson_util.errormodel_json(num,code=401,msg='上传图片出现异常:'+str(e),taskId=fundata["taskId"])
           
    print('文生图执行完成') 
    num.value = 1  # 子进程改变数值的值，主进程跟着改变
    print('子线程2：',num.value)
    print('子线程处理完成')
