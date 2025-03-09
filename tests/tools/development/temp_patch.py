
import sys
import builtins

# ����__import__�֐���ۑ�
original_import = builtins.__import__

# ���Z�b�g�񐔃J�E���^�[
reset_count = 0
MAX_RESET_COUNT = 5

# �A�h�o�^�C�Y���[�h�𐧌�����֐�
def limited_advertise_mode():
    global reset_count
    reset_count += 1
    print(f"�A�h�o�^�C�Y���[�h����: {reset_count}/{MAX_RESET_COUNT}")
    if reset_count >= MAX_RESET_COUNT:
        print("�ő�A�h�o�^�C�Y�񐔂ɒB�������ߏI�����܂�")
        sys.exit(0)

# �C���|�[�g�����j�^�����O����֐�
def patched_import(name, *args, **kwargs):
    module = original_import(name, *args, **kwargs)
    
    # main���W���[���̏ꍇ�A�A�h�o�^�C�Y���[�h�𐧌�
    if name == 'main':
        if hasattr(module, 'advertise_mode'):
            module.advertise_mode = limited_advertise_mode
            print("main���W���[���̃A�h�o�^�C�Y���[�h�𐧌����܂���")
    
    return module

# __import__�֐���u������
builtins.__import__ = patched_import
