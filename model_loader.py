import tensorflow as tf
from model.model import get_model

# 모델 설정(config)
config = {
    # model
    'input_shape': [256,256,5],     # 훈련 이미지 크기
    'batch_size': 1,                # 배치 사이즈
    'path_pretrained': None,        # pretrained 모델 경로
    'type_backbone': "blazepose",   # backbone type
    
    # loss
    'type_loss_fn': 'wing',         # 손실 함수 설정 (wing, mae)
    
    # data
    'seg_shape': [64,64],           # segmentation 크기 *미사용
    'path_classes': "../seg_classes.txt",   # segmentation class 정보 *미사용
    'shuffle': True,                # 데이터 섞기
    'is_normalized': False,         # normalize 데이터
    'is_with_seg': True,           # segmentation 사용 여부 *미사용

    ## attention type              
    'type_attention': "regression", # attention 종류 (regression, categorical, none)
    'has_filename': False,
}
# 모델 초기화 및 가중치 로드
def load_model():
    model = get_model(config)
    model.load_weights(r'C:\Users\kangsei\Desktop\학교 수업\1학년 2학기\융프\Final_Application\blazepose_attention_seg_10_3.1590578383293706.h5')  # 모델 가중치 경로
    return model

