import os

def execute(global_data,**kargs):

    content = "src/content"
    blogdir = "blogposts"

    global_data['blogposts'] = [os.path.join(blogdir, f) for f in os.listdir("src/content/blogposts") if os.path.isfile(os.path.join(content, blogdir, f)) and (f.endswith(".md") or f.endswith(".rst") or f.endswith(".html")) ]
    print("INIT:",global_data['blogposts'])
