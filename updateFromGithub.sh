changed=0
git remote update && git status -uno | grep -q 'Your branch is behind' && changed=1
if [ $changed = 1 ]; then
    #git pull
    git reset --hard @{u}
    sudo systemctl restart PiClock.service
fi
