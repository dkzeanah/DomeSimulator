"""Export one lesson to a narrated MP4 through the real launcher path."""

import sys
sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

import launcher_common as lc
from two_v_demo.app import main

key, out = sys.argv[1], sys.argv[2]
lc.write_config("two_v_masterclass", {
    "action": "export_video",
    "lesson": key,
    "export_video": out,
    "size": "1920x1080",
    "fps": 30,
})
raise SystemExit(main())
