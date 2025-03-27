# 超星学习通Web管理面板
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import sys

# 确保可以导入主项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 