from flask import Flask, request, render_template, send_from_directory, jsonify
import os
import subprocess
import uuid

app = Flask(__name__)

# 配置上传文件夹和允许的文件扩展名
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'presentation_output'
ALLOWED_EXTENSIONS = {'pdf', 'json'} # 允许PDF和JSON输入
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 确保目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_presentation():
    """处理文件上传和演示文稿生成"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # 为上传的文件生成一个安全的文件名和唯一的ID
        original_filename = file = file.filename
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{original_filename}")
        file.save(input_path)

        # 根据文件类型确定要调用的脚本和输出文件名
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        output_filename = f"{os.path.splitext(original_filename)[0]}_{unique_id}.pptx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        script_to_run = ''
        # 假设我们有一个脚本可以处理PDF，另一个处理JSON
        # 现在我们主要关注 create_ai_ppt.py，它需要JSON
        # 我们需要修改它来接收文件路径而不是字符串
        if file_ext == 'json':
            script_to_run = os.path.join('scripts', 'create_ai_ppt.py')
        elif file_ext == 'pdf':
            # 假设 create_pdf_presentation.py 可以处理PDF
            # script_to_run = os.path.join('scripts', 'create_pdf_presentation.py')
            return jsonify({"error": "PDF processing not implemented yet."}), 501
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        try:
            # 使用subprocess调用现有的Python脚本
            # 我们需要向脚本传递输入文件路径和期望的输出文件路径
            # 这要求我们对原脚本进行修改
            print(f"Running script: {script_to_run} with input {input_path} and output {output_path}")
            subprocess.run([
                'python',
                script_to_run,
                '--input', input_path,
                '--output', output_path
            ], check=True)

            # 返回成功响应和下载链接
            return jsonify({
                "success": True,
                "download_url": f"/download/{output_filename}"
            })

        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"An error occurred during presentation generation: {e}"}), 500
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    return jsonify({"error": "File type not allowed"}), 400

@app.route('/download/<filename>')
def download_file(filename):
    """提供生成文件的下载"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
