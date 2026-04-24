#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime

# --- 設定 ---
BASE_DIR_NAME = "math_session"
MATH_COMMAND = "math"      # 環境に合わせて "wolfram" 等に変更
PREVIEW_FILE = "preview.png" # プレビュー用の画像ファイル名（これは一時ファイル）

# PDFを開くコマンド
def open_pdf(pdf_path):
    print(f"--- Opening {pdf_path} ... ---")
    kwargs = {}
    if sys.platform != "win32":
        kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}

    if sys.platform == "darwin":       # macOS
        subprocess.Popen(["open", pdf_path], **kwargs)
    elif os.name == "nt":              # Windows
        os.startfile(pdf_path)
    else:                              # Linux / Unix
        try:
            subprocess.Popen(["xdg-open", pdf_path], **kwargs)
        except FileNotFoundError:
            try:
                subprocess.Popen(["evince", pdf_path], **kwargs)
            except:
                pass

def create_session_directory(base):
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{base}_{now_str}"
    counter = 1
    original_dir_name = dir_name
    while os.path.exists(dir_name):
        dir_name = f"{original_dir_name}_{counter}"
        counter += 1
    os.makedirs(dir_name)
    return dir_name

def finalize_log_file(filename):
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(r"\end{document}" + "\n")
    except IOError:
        pass

def compile_to_pdf(tex_path):
    """
    tex_path: ディレクトリを含むパス
    """
    print(f"\n--- Compiling {tex_path} ... ---")
    abs_tex_path = os.path.abspath(tex_path)
    work_dir = os.path.dirname(abs_tex_path)
    tex_file = os.path.basename(abs_tex_path)
    base_root, _ = os.path.splitext(tex_file)
    
    dvi_filename = base_root + ".dvi"
    pdf_filename = base_root + ".pdf"

    try:
        # platex 実行 (ディレクトリ内で実行)
        subprocess.call(["platex", "-interaction=nonstopmode", tex_file], 
                         cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not os.path.exists(os.path.join(work_dir, dvi_filename)):
             print("Error: platex failed. Check source file.")
             return

        # dvipdfmx 実行
        print(f"--- Converting to PDF ({pdf_filename}) ... ---")
        ret_dvipdf = subprocess.call(["dvipdfmx", dvi_filename],
                                     cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if ret_dvipdf != 0:
            print("Error: dvipdfmx conversion failed.")
            return

        # 3. PDF Open
        full_pdf_path = os.path.join(work_dir, pdf_filename)
        if os.path.exists(full_pdf_path):
            open_pdf(full_pdf_path)
            print("--- Done. Exiting script immediately. ---")

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # 1. セッションディレクトリの準備
    session_dir = create_session_directory(BASE_DIR_NAME)
    log_filename = "main.tex"
    log_path = os.path.join(session_dir, log_filename)
    
    # 絶対パスの取得（Mathematicaへの受け渡し用）
    log_file_abs = os.path.abspath(log_path).replace("\\", "/")
    img_dir_abs = os.path.abspath(session_dir).replace("\\", "/")
    
    # プレビューファイルはカレントディレクトリに一時的に置く
    cwd = os.getcwd().replace("\\", "/")
    preview_abs = f"{cwd}/{PREVIEW_FILE}"

    # OSごとの「画像を開くコマンド」
    if sys.platform == "darwin": # Mac
        popup_cmd = f"open -g {preview_abs}"
    elif os.name == "nt":        # Windows
        popup_cmd = f"cmd /c start {preview_abs}"
    else:                        # Linux
        popup_cmd = f"xdg-open {preview_abs} > /dev/null 2>&1 &"

    # LaTeXヘッダー作成
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(r"\documentclass{article}" + "\n")
            f.write(r"\usepackage[dvipdfmx]{graphicx}" + "\n")
            f.write(r"\usepackage{amsmath, amssymb}" + "\n")
            f.write(r"\usepackage[margin=1in]{geometry}" + "\n")
            f.write(r"\setlength{\parindent}{0pt}" + "\n")
            f.write(r"\begin{document}" + "\n")
            f.write(f"\\section*{{Mathematica Log: {session_dir}}}" + "\n")
            
    except IOError as e:
        print(f"Error initializing log file: {e}")
        sys.exit(1)

    # 2. Mathematica 注入コード
    inject_code = f"""
    logFile = "{log_file_abs}";
    imgDir = "{img_dir_abs}/";
    previewFile = "{preview_abs}";
    popupCmd = "{popup_cmd}";
    imgCounter = 0;

    IsGraphic[expr_] := MemberQ[{{Graphics, Graphics3D, Graph, Image, Legended, ContourGraphics, SurfaceGraphics, DensityGraphics}}, Head[expr]];

    WriteLog[expr_] := Module[{{strIn, strOut, stream, imgName, relImgName, safeImgName}},
        strIn = InString[$Line];
        If[!StringQ[strIn], strIn = ToString[InputForm[In[$Line]]]];

        stream = OpenAppend[logFile];
        
        WriteString[stream, 
            "\\\\begin{{verbatim}}\\n" <> 
            "In[" <> ToString[$Line] <> "]:= " <> strIn <> "\\n" <> 
            "\\\\end{{verbatim}}\\n"
        ];

        If[expr =!= Null,
            If[IsGraphic[expr],
                (* --- グラフ --- *)
                imgCounter++;
                
                (* 1. 本番用(JPG)保存 *)
                imgName = imgDir <> "img" <> ToString[imgCounter] <> ".jpg";
                Export[imgName, expr, "JPG"];
                
                (* 2. プレビュー用(PNG)保存 *)
                Export[previewFile, expr, "PNG"];

                (* 3. ポップアップ実行 *)
                Run[popupCmd];

                (* ログ書き込み (ディレクトリ内なのでファイル名のみ) *)
                relImgName = "img" <> ToString[imgCounter] <> ".jpg";
                WriteString[stream, "\\\\begin{{center}}\\\\includegraphics[width=10cm]{{" <> relImgName <> "}}\\\\end{{center}}\\n"];
                WriteString[stream, "\\\\noindent -Graphics- (Saved as " <> relImgName <> ")\\n\\n"];
            ,
                (* --- 数式 --- *)
                strOut = ToString[TeXForm[expr]];
                WriteString[stream, "\\\\[ " <> strOut <> " \\\\]\\n\\n"];
            ];
        ];
        
        Close[stream];
        expr
    ];
    $Post = WriteLog;
    """

    run_code = inject_code.replace("\n", " ").strip()

    print(f"--- Starting Mathematica ---")
    print(f"--- Session Directory: {session_dir} ---")
    print(f"--- Preview Mode: Graphs will popup as '{PREVIEW_FILE}' ---")

    # 3. Mathematica 実行
    try:
        subprocess.call([MATH_COMMAND, "-run", run_code])
    except FileNotFoundError:
        print(f"Error: Command '{MATH_COMMAND}' not found.")
        return
    except KeyboardInterrupt:
        print("\nInterrupted.")
    
    # 4. 終了処理
    finalize_log_file(log_path)
    compile_to_pdf(log_path)
    
    # お掃除
    if os.path.exists(preview_abs):
        try:
            os.remove(preview_abs)
        except:
            pass

if __name__ == "__main__":
    main()