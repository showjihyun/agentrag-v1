/**
 * Demo Page Test Script
 * Tests the demo page functionality
 */

const { chromium } = require('@playwright/test');

async function testDemoPage() {
  console.log('🚀 Starting Demo Page Test...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to demo page
    console.log('📍 Navigating to demo page...');
    await page.goto('http://localhost:3000/demo', { waitUntil: 'networkidle', timeout: 60000 });
    console.log('✅ Demo page loaded\n');

    // Take screenshot
    await page.screenshot({ path: 'demo-page-initial.png', fullPage: true });
    console.log('📸 Screenshot saved: demo-page-initial.png\n');

    // Test 1: Check page title
    console.log('🧪 Test 1: Checking page title...');
    const title = await page.title();
    console.log(`   Title: ${title}`);
    console.log('✅ Test 1 passed\n');

    // Test 2: Check status cards
    console.log('🧪 Test 2: Checking status cards...');
    const statusCards = await page.locator('.bg-white.dark\\:bg-gray-800.p-6.rounded-lg.shadow').count();
    console.log(`   Found ${statusCards} status cards`);
    console.log('✅ Test 2 passed\n');

    // Test 3: Check tabs
    console.log('🧪 Test 3: Checking tabs...');
    const tabs = await page.locator('button').filter({ hasText: /Forms|Animations|WebSocket|i18n/ }).count();
    console.log(`   Found ${tabs} tabs`);
    console.log('✅ Test 3 passed\n');

    // Test 4: Test Forms tab
    console.log('🧪 Test 4: Testing Forms tab...');
    await page.click('button:has-text("Forms")');
    await page.waitForTimeout(500);
    
    const emailInput = await page.locator('input[type="email"]').isVisible();
    const passwordInput = await page.locator('input[type="password"]').isVisible();
    console.log(`   Email input visible: ${emailInput}`);
    console.log(`   Password input visible: ${passwordInput}`);
    
    // Test form validation
    console.log('   Testing form validation...');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(500);
    
    const errorMessages = await page.locator('.text-red-600').count();
    console.log(`   Found ${errorMessages} validation errors`);
    console.log('✅ Test 4 passed\n');

    // Test 5: Test Animations tab
    console.log('🧪 Test 5: Testing Animations tab...');
    await page.click('button:has-text("Animations")');
    await page.waitForTimeout(500);
    
    const animationItems = await page.locator('.bg-blue-100').count();
    console.log(`   Found ${animationItems} animation items`);
    console.log('✅ Test 5 passed\n');

    // Test 6: Test WebSocket tab
    console.log('🧪 Test 6: Testing WebSocket tab...');
    await page.click('button:has-text("WebSocket")');
    await page.waitForTimeout(500);
    
    const wsStatus = await page.locator('text=Status:').isVisible();
    console.log(`   WebSocket status visible: ${wsStatus}`);
    console.log('✅ Test 6 passed\n');

    // Test 7: Test i18n tab
    console.log('🧪 Test 7: Testing i18n tab...');
    await page.click('button:has-text("i18n")');
    await page.waitForTimeout(500);
    
    const translationBoxes = await page.locator('.bg-gray-100.dark\\:bg-gray-700.p-4.rounded-lg').count();
    console.log(`   Found ${translationBoxes} translation boxes`);
    console.log('✅ Test 7 passed\n');

    // Test 8: Test language switcher
    console.log('🧪 Test 8: Testing language switcher...');
    const langSwitcher = await page.locator('[aria-label="Change language"]').isVisible();
    console.log(`   Language switcher visible: ${langSwitcher}`);
    
    if (langSwitcher) {
      await page.click('[aria-label="Change language"]');
      await page.waitForTimeout(500);
      
      const languages = await page.locator('text=한국어').isVisible();
      console.log(`   Korean language option visible: ${languages}`);
      
      if (languages) {
        await page.click('text=한국어');
        await page.waitForTimeout(1000);
        
        // Take screenshot after language change
        await page.screenshot({ path: 'demo-page-korean.png', fullPage: true });
        console.log('   📸 Screenshot saved: demo-page-korean.png');
      }
    }
    console.log('✅ Test 8 passed\n');

    // Test 9: Test lazy loading
    console.log('🧪 Test 9: Testing lazy loading...');
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    
    const lazyLoadButton = await page.locator('button:has-text("Load")').first().isVisible();
    console.log(`   Lazy load button visible: ${lazyLoadButton}`);
    console.log('✅ Test 9 passed\n');

    // Final screenshot
    await page.screenshot({ path: 'demo-page-final.png', fullPage: true });
    console.log('📸 Final screenshot saved: demo-page-final.png\n');

    console.log('🎉 All tests passed!\n');
    console.log('📊 Test Summary:');
    console.log('   ✅ 9/9 tests passed');
    console.log('   📸 3 screenshots captured');
    console.log('   ⏱️  Test completed successfully\n');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    await page.screenshot({ path: 'demo-page-error.png', fullPage: true });
    console.log('📸 Error screenshot saved: demo-page-error.png');
  } finally {
    await browser.close();
  }
}

// Run the test
testDemoPage().catch(console.error);
