'use strict';
// Synthetic offline probe of a supplied approval CLI source checkout. No real keys,
// remote fetches, forceApprove helper, or approval-state edits are used.
const fs=require('fs'),os=require('os'),path=require('path'),cp=require('child_process');
async function runScenario({source,frozen=false,rejectSecondRow=false}={}){
  const {createEngine}=require(path.join(source,'src/dispatch-engine'));
  const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'ep-signed-approval-probe-'));
  try{
    const codeRoot=path.join(temporary,'code'),dataDir=path.join(temporary,'canonical-test-data');
    fs.mkdirSync(codeRoot);
    for(const directory of ['src','schemas','config'])fs.cpSync(path.join(source,directory),path.join(codeRoot,directory),{recursive:true});
    const jobId='EP-APPROVAL-SYNTHETIC-TEST',revision='2026-10-05T17:00:00.000Z';
    const engine=createEngine({dataDir});
    const envelope={schema_version:'1.0',job_id:jobId,idempotency_key:'synthetic-approval-probe:1',
      objective:'Synthetic signed approval CLI probe only.',owning_project:'synthetic-test',requested_by:'local-test',
      created_at:revision,due_at:null,priority:'P2',current_verified_state:'No live assignment.',
      source_manifest:[{source_id:'drive:synthetic-approval-doc',revision,kind:'google_doc'}],
      scope:['Local test only.'],explicit_exclusions:['No live writes or credentials.'],requirements:['Exercise actual signed approval.'],
      constraints:['No spending.'],data_class:'INTERNAL',authorized_source_ids:['drive:synthetic-approval-doc'],execution_lane:'deterministic',
      repository:null,acceptance_criteria:['Gate result observed.'],required_tests:['Offline CLI probe.'],required_evidence:['Probe result.'],
      rollback:'Delete temporary state.',stop_conditions:['Any real network request.'],protected_actions:['deploy'],
      cost_policy:{metered_calls_allowed:false,max_job_usd:0,max_call_usd:null},
      authorization_binding:{command_center_job_id:jobId,drive_file_id:'synthetic-approval-doc',drive_revision:revision,
      drive_doc_url:'https://docs.google.com/document/d/synthetic-approval-doc/edit'},dependencies:[]};
    const ingested=await engine.ingestJobEnvelope(envelope),taskId=ingested.handoff.task_id;
    if(engine.getHandoff(taskId).status!=='ROUTED')throw new Error('Fixture did not enter ROUTED through real ingest');
    const preload=path.join(temporary,'preload.cjs');
    fs.writeFileSync(preload,String.raw`
      const fs=require('fs'),path=require('path'),crypto=require('crypto');
      const codeRoot=process.env.EP_SYNTHETIC_CODE_ROOT;
      if(process.env.EP_SYNTHETIC_FROZEN_TIME==='true'){
        const ActualDate=Date,fixed=Date.parse('2026-10-05T17:01:00.000Z');
        global.Date=class extends ActualDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};
      }
      const pair=crypto.generateKeyPairSync('ed25519');
      const publicKeyPem=pair.publicKey.export({type:'spki',format:'pem'});
      const privateKeyPem=pair.privateKey.export({type:'pkcs8',format:'pem'});
      fs.writeFileSync(path.join(codeRoot,'config/trusted-producer-keys.json'),JSON.stringify([{keyId:'synthetic-approval-key',publicKeyPem,effectiveFrom:'2020-01-01T00:00:00Z',revokedAt:null}]));
      const auth=require(path.join(codeRoot,'src/dispatch-drive-auth'));
      const rsa=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
      auth.resolveDriveCredential=async()=>({clientEmail:'synthetic@invalid.iam.gserviceaccount.com',privateKey:rsa.privateKey.export({type:'pkcs1',format:'pem'})});
      const producer=require(path.join(codeRoot,'src/dispatch-producer-auth'));
      producer.loadProducerPrivateKey=()=>privateKeyPem;
      let sheetsRequests=0;
      global.fetch=async(url)=>{
        await new Promise(resolve=>setTimeout(resolve,8));
        if(url===auth.TOKEN_URL)return {ok:true,status:200,json:async()=>({access_token:'synthetic-local-only-token',expires_in:3600})};
        if(url.includes('sheets.googleapis.com')){sheetsRequests++;return {ok:true,status:200,json:async()=>({values:[['Job ID','Project / Domain','Worker','Job / Outcome','Execution State'],['EP-APPROVAL-SYNTHETIC-TEST','Synthetic','ChatGPT','Offline only',(process.env.EP_SYNTHETIC_REJECT_SECOND_ROW==='true'&&sheetsRequests>1)?'ROUTED':'APPROVED_FOR_EXECUTION']]})};}
        if(url.includes('/export'))return {ok:true,status:200,text:async()=> 'JOB_ID: EP-APPROVAL-SYNTHETIC-TEST\nAUTHORIZED_BY: synthetic-test\nNo live authorization.'};
        if(url.startsWith('https://www.googleapis.com/drive/v3/files/'))return {ok:true,status:200,json:async()=>({id:'synthetic-approval-doc',modifiedTime:'2026-10-05T17:00:00.000Z',mimeType:'application/vnd.google-apps.document'})};
        throw new Error('Unexpected URL rejected by offline probe');
      };
    `);
    const invoked=cp.spawnSync(process.execPath,['--require',preload,path.join(codeRoot,'src/dispatch-cli.js'),'approve-for-execution',taskId,'--key-id=synthetic-approval-key'],{
      env:{NODE_ENV:'production',ORCHESTRATOR_DATA_DIR:dataDir,EP_SYNTHETIC_CODE_ROOT:codeRoot,EP_SYNTHETIC_FROZEN_TIME:String(frozen),EP_SYNTHETIC_REJECT_SECOND_ROW:String(rejectSecondRow)},encoding:'utf8',timeout:10000});
    if(invoked.signal||invoked.error)throw new Error('Synthetic CLI process failed to complete');
    let returned;
    try{returned=JSON.parse(invoked.stdout);}catch{throw new Error('Synthetic CLI produced no result');}
    return {scenario:rejectSecondRow?'fresh-command-center-rejection':(frozen?'fixed-test-clock':'advancing-real-clock'),cliExitCode:invoked.status,
      approvalOk:returned.ok,approvalReason:returned.reason,persistedStatus:engine.getHandoff(taskId).status,
      canonicalTemporaryDataDir:true,realNetworkRequests:0,realCredentialsUsed:0};
  }finally{fs.rmSync(temporary,{recursive:true,force:true});}
}
module.exports={runScenario};
if(require.main===module){
  (async()=>{
    const source=process.env.BOS_SOURCE_DIR||process.env.BOS_REFERENCE_DIR||process.argv[2];
    if(!source)throw new Error('Supply BOS_SOURCE_DIR or BOS_REFERENCE_DIR');
    const results=[await runScenario({source}),await runScenario({source,frozen:true}),await runScenario({source,rejectSecondRow:true})];
    const expected=process.argv.find(value=>value.startsWith('--expect='))?.split('=')[1];
    let expectationSatisfied=null;
    if(expected){
      if(!['baseline','patched'].includes(expected))throw new Error('Invalid expected mode');
      expectationSatisfied=expected==='baseline'
        ? results[0].approvalOk===false&&results[0].approvalReason==='producer_signature_signature_invalid'&&results[0].cliExitCode===0&&results[1].approvalOk===true&&results[2].cliExitCode===0
        : results[0].approvalOk===true&&results[0].cliExitCode===0&&results[1].approvalOk===true&&results[2].approvalOk===false&&results[2].cliExitCode===1;
      if(!expectationSatisfied)process.exitCode=1;
    }
    console.log(JSON.stringify({source,expected:expected||null,expectationSatisfied,results},null,2));
  })().catch(()=>{console.error('Offline approval probe failed safely.');process.exitCode=1;});
}
