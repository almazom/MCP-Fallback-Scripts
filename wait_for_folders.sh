#!/bin/bash

echo "🔄 Waiting for Google Drive shared folders to become available..."
echo "This can take 5-10 minutes after sharing..."

export PATH="$HOME/.local/bin:$PATH"

for i in {1..30}; do
    echo "⏳ Check $i/30: Looking for shared folders..."
    
    # Check if we can see any folders
    folders=$(rclone lsd mydrive: 2>/dev/null)
    
    if [ ! -z "$folders" ]; then
        echo "✅ Shared folders are now visible!"
        echo "$folders"
        echo ""
        echo "🎉 You can now use these commands:"
        echo "./gdrive_manager.sh list Plaude"
        echo "./gdrive_manager.sh list 'api test'"
        break
    else
        echo "⌛ Still waiting... (attempt $i/30)"
        sleep 20
    fi
done

if [ -z "$folders" ]; then
    echo "⚠️  Folders still not visible after 10 minutes."
    echo "This is normal - sometimes Google takes longer."
    echo "Try running: ./gdrive_manager.sh list"
fi