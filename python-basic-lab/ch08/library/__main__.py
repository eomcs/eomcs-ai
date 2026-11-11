"""python -m library로 실행했을 때 실행되는 모듈.

이 파일은 import될 일이 없으므로 if __name__ == "__main__":으로 감싸지 않는다.
내용은 cli.main()에 맡기고 호출만 한다(8.3.4).
"""

from library.cli import main

main()
