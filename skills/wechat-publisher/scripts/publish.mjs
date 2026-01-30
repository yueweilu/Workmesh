import fs from 'fs';
import { exec } from 'child_process';
import path from 'path';
import https from 'https';

// Function to perform the publish request directly using Node.js https module
function publishArticle(mediaId, accessToken) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({
            media_id: mediaId
        });

        const options = {
            hostname: 'api.weixin.qq.com',
            path: `/cgi-bin/freepublish/submit?access_token=${accessToken}`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    if (result.errcode === 0) {
                        resolve(result);
                    } else {
                        reject(new Error(`WeChat API Error: ${result.errmsg} (code: ${result.errcode})`));
                    }
                } catch (e) {
                    reject(new Error(`Failed to parse response: ${data}`));
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        req.write(postData);
        req.end();
    });
}

// Function to get Access Token using simple fetch
function getAccessToken(appId, appSecret) {
    return new Promise((resolve, reject) => {
        https.get(`https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    if (result.access_token) {
                        resolve(result.access_token);
                    } else {
                        reject(new Error(`Failed to get token: ${result.errmsg}`));
                    }
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', (e) => reject(e));
    });
}

async function main() {
  console.log('🚀 Starting WeChat Automation (CLI Mode)...');

  try {
    // 1. Load Config
    // Use absolute path or relative to this script
    const __dirname = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([a-zA-Z]:)/, '$1'); // Handle Windows path
    const configPath = path.resolve(__dirname, '../assets/wechat_config.json');
    
    if (!fs.existsSync(configPath)) {
        throw new Error(`wechat_config.json not found at ${configPath}`);
    }
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    
    if (!config.appId || !config.appSecret) {
        throw new Error("AppID or AppSecret missing in config");
    }

    console.log('📖 Config loaded for AppID: ' + config.appId);

    // 2. Prepare Environment Variables
    const env = {
        ...process.env,
        WECHAT_APP_ID: config.appId.trim(),
        WECHAT_APP_SECRET: config.appSecret.trim(),
        WECHAT_DEFAULT_AUTHOR: "MAX",
        WECHAT_NEED_OPEN_COMMENT: "true"
    };

    // 3. Execute CLI Command to Create Draft
    // Pointing to the installation in D:\MAX_Workspace
    const cliPath = 'D:\\MAX_Workspace\\node_modules\\@lanyijianke\\wechat-official-account-mcp\\build\\index.js';
    
    // Get arguments passed to this script (skipping node and script path)
    const args = process.argv.slice(2);
    
    // Default to test-connection if no args provided
    const cliArgs = args.length > 0 ? args.join(' ') : 'test-connection';
    
    const command = `node "${cliPath}" ${cliArgs}`;

    console.log(`🔑 Running command: ${cliArgs}...`);
    
    exec(command, { env }, async (error, stdout, stderr) => {
        if (error) {
            console.error('❌ Execution Error');
            console.log(stdout);
            console.error(stderr);
            return;
        }
        console.log(`✅ Draft Created Output:\n${stdout}`);

        // 4. Check if it was a push command and extract Media ID
        // The regex needs to match the Chinese output: 媒体ID: xxxxx
        if (cliArgs.includes('push-')) {
            const mediaIdMatch = stdout.match(/媒体ID:\s*([a-zA-Z0-9_-]+)/);
            if (mediaIdMatch && mediaIdMatch[1]) {
                const mediaId = mediaIdMatch[1];
                console.log(`🎯 Detected Media ID: ${mediaId}`);
                console.log('🚀 Initiating Auto-Publish...');

                try {
                    const token = await getAccessToken(config.appId, config.appSecret);
                    console.log('🔑 Access Token retrieved.');
                    
                    const publishResult = await publishArticle(mediaId, token);
                    console.log('🎉 PUBLISH SUCCESS!');
                    console.log(`🆔 Publish ID: ${publishResult.publish_id}`);
                    if(publishResult.msg_data_id) {
                         console.log(`📄 Msg Data ID: ${publishResult.msg_data_id}`);
                    }

                } catch (pubError) {
                    console.error(`❌ Publish Failed: ${pubError.message}`);
                    if (pubError.message.includes('48001')) {
                         console.error('💡 Hint: Check API permissions or if "Publish" interface is enabled.');
                    }
                }
            } else {
                console.log('⚠️ Could not extract Media ID from output. Skipping auto-publish.');
            }
        }
    });

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

main();